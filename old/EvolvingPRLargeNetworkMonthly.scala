#!/bin/sh
exec scala -J-Xmx6g -classpath ".:$GRAPHSLICES_JAR" "$0" "$@"
!#

import java.io.{File, PrintWriter}

import org.zviri.graphslices.{Algorithms, Edge, Graph, IOUtil, Vertex}
import org.joda.time.{LocalDate, Months}
import org.joda.time.format.DateTimeFormat
import play.api.libs.json.{JsValue, Json, OFormat}
import scala.io.Source
import scala.util.Try

case class NodeIsir(id: Long, stringId: String, name: String, personType: String, regionId: Option[Long], nodeType: String, date: Option[LocalDate])

case class EdgeIsir(srcId: Long, dstId: Long, edgeType: String, startDate: LocalDate, endDate: Option[LocalDate])

case class JsonLine(id: Long, stringId: String, nodeType: String, pr: Seq[(Long, Double)], prEvolvingQuad: Seq[(Long, Double)], prEvolving: Seq[(Long, Double)])

object JsonLine {
  implicit def format: OFormat[JsonLine] = Json.format[JsonLine]
}

val dateFormat = DateTimeFormat.forPattern("yyyy-MM-dd")
val dataDir = sys.env("EXPERIMENTS_DATA_FOLDER")

println("Loading nodes...")
val nodesIsir = Source.fromFile(
  s"${dataDir}/isir/nodes_2018_04_09.tsv"
).getLines().drop(1).map(
  row => row.split("\t", 6)
).map {
  case Array(id, name, personType, regionId, type_, date) =>
    NodeIsir(id.hashCode, id, name, personType, Try(regionId.toDouble.toLong).toOption, type_, Try(dateFormat.parseLocalDate(date)).toOption)
}.toVector.distinct

println("Loading edges...")
val nodesSet = nodesIsir.map(_.id).toSet
val edgesIsir = Source.fromFile(
  s"${dataDir}/isir/edges_2018_04_09.tsv"
).getLines().drop(1).map(
  row => row.split("\t", 5)
).map {
  case Array(srcId, dstId, type_, startDate, endDate) =>
    EdgeIsir(srcId.hashCode, dstId.hashCode, type_, dateFormat.parseLocalDate(startDate), Try(dateFormat.parseLocalDate(endDate)).toOption)
}.toVector.filter(
  e => nodesSet.contains(e.srcId) && nodesSet.contains(e.dstId)
).groupBy(
  e => (e.srcId, e.dstId)
).map {
  case (key, grp) => grp.head
}

val vertices = nodesIsir.map(n => Vertex(Seq(n.id), n)).toVector
val edges = edgesIsir.zipWithIndex.map {
  case (e, idx) => Edge(Seq(idx), Seq(e.srcId), Seq(e.dstId), e)
}.toVector

println("Selecting subgraph Kraj Vysocina")
val REGION_ID = 3l
val loadGraph = Graph(vertices, edges).subgraph(
  edgePredicate = triplet => triplet.srcVertex.data.regionId.getOrElse(-1) == REGION_ID || triplet.dstVertex.data.regionId.getOrElse(-1) == REGION_ID
)
val filteredGraph = loadGraph.outerJoinVertices(Algorithms.degree(loadGraph).vertices.map(v => (v.id, v.data))) {
  (vertex, degree) => (vertex.data, degree.get)
}.subgraph(vertexPredicate = v => v.data._2 > 0).mapVertices(_.data._1)

println(s"Number of vertices: ${loadGraph.vertices.size}")
println(s"Number of edges: ${loadGraph.edges.size}")


val computeGraph = filteredGraph.mapVertices(v => Unit).pushDimension[Double](
  e => {
    val edge = e.data
    val numMonthsActive = Months.monthsBetween(edge.startDate, edge.endDate.getOrElse(LocalDate.now())).getMonths
    (0 to numMonthsActive).map(edge.startDate.plusMonths).map(
      date => (date.year.get * 100 + date.monthOfYear.get.toLong, 1.0)
    )
  }, keepAllNodes = true
)

println("Running PageRank algorithm...")
var start = System.currentTimeMillis
val graphPr = Algorithms.pagerank(
  computeGraph, numIter = 100
).popDimension(
  vs => vs.map { case (topKey, key, pr) => (topKey, pr) }.sorted, es => Unit
)
var runtime = (System.currentTimeMillis - start) / 1000.0
println(s"PageRank finished in ${runtime} seconds.")
val prMap = graphPr.vertices.map(v => (v.id.head, v.data)).toMap

println("Running evolving PageRank algorithm (1/(t*t))...")
start = System.currentTimeMillis
val graphPrTimeQuad = Algorithms.evolvingPagerank(
  computeGraph,
  timeDecayFunc = (time: Double) => 1.0 / (time * time),
  numIter = 100
)
runtime = (System.currentTimeMillis - start) / 1000.0
println(s"PageRank finished in ${runtime} seconds.")
val quadEvolvingPrMap = graphPrTimeQuad.vertices.map(v => (v.id.head, v.data)).toMap

println("Running evolving PageRank algorithm (1/t)...")
start = System.currentTimeMillis
val graphPrTime = Algorithms.evolvingPagerank(
  computeGraph,
  timeDecayFunc = (time: Double) => 1.0 / time,
  numIter = 100
)
runtime = (System.currentTimeMillis - start) / 1000.0
println(s"PageRank finished in ${runtime} seconds.")
val evolvingPrMap = graphPrTime.vertices.map(v => (v.id.head, v.data)).toMap

val jsonLines = graphPr.outerJoinVertices[NodeIsir, JsValue](nodesIsir.map(v => (Seq(v.id), v))) {
  (vertex, dataOption) => {
    val data = dataOption.get
    val id = vertex.id.head
    val row = JsonLine(id, data.stringId, data.nodeType, prMap(id), quadEvolvingPrMap(id), evolvingPrMap(id))
    Json.toJson(row)
  }
}.vertices.map(_.data)

IOUtil.saveJsonLine(s"${dataDir}/evolving_pagerank_large_graph_monthly_experiment.jsonline", jsonLines)

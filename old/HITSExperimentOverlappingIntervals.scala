#!/bin/sh
exec scala -J-Xmx6g -classpath ".:$GRAPHSLICES_JAR" "$0" "$@"
!#

import java.io.{File, PrintWriter}

import org.joda.time.LocalDate
import org.joda.time.format.DateTimeFormat

import scala.io.Source
import scala.util.Try
import org.zviri.graphslices.Algorithms.HitsScore
import org.zviri.graphslices.{Algorithms, Edge, Graph, Vertex}

case class NodeIsir(id: Long, stringId: String, name: String, personType: String, regionId: Option[Long], nodeType: String, date: Option[LocalDate])

case class EdgeIsir(srcId: Long, dstId: Long, edgeType: String, startDate: LocalDate, endDate: Option[LocalDate])

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
  edgePredicate = triplet => triplet.srcVertex.data.regionId.getOrElse(-1) == REGION_ID || triplet.dstVertex.data.regionId.getOrElse(-1) == REGION_ID,
)
val filteredGraph = loadGraph.outerJoinVertices(Algorithms.degree(loadGraph).vertices.map(v => (v.id, v.data))) {
  (vertex, degree) => (vertex.data, degree.get)
}.subgraph(vertexPredicate = v => v.data._2 > 0).mapVertices(_.data._1)

println(s"Number of vertices: ${loadGraph.vertices.size}")
println(s"Number of edges: ${loadGraph.edges.size}")

val computeGraph = filteredGraph.mapVertices(v => Unit).pushDimension[Double](
  e => {
    val edge = e.data
    (0 to 11).map(
      edge.startDate.plusMonths
    ).filter(
      d => d.isBefore(edge.endDate.getOrElse(LocalDate.now))
    ).zipWithIndex.map {
      case (date, idx) =>
        (date.year.get * 100 + date.monthOfYear.get.toLong, Math.pow(1 * (1 - 0.9), idx / 11.0))
    }
  }
)

println("Running HITS algorithm...")
val start = System.currentTimeMillis

val graphHA = Algorithms.hits(
  computeGraph, numIter = 100
).popDimension(vs => vs.map(v => (v._1, v._3)).toMap, es => Unit)
val runtime = (System.currentTimeMillis - start) / 1000.0
println(s"HITS finished in ${runtime} seconds.")

val writer = new PrintWriter(new File(s"${dataDir}/hits_overlapping_intervals.jsonline"))
graphHA.outerJoinVertices[NodeIsir, Int](nodesIsir.map(v => (Seq(v.id), v))) {
  (vertex, dataOption) => {
    val data = dataOption.get
    var row = s"""{"id": "${data.stringId}", "type": "${data.nodeType}", """
    row = row + (""" "scores": [""" + vertex.data.toList.sortBy(_._1).map {
      case (k, v) => s""" {"date": "$k\", "hub": ${v.hub}, "authority": ${v.authority}}"""
    }.mkString(", ") + "]}")
    writer.println(row)
    1
  }
}
writer.close()

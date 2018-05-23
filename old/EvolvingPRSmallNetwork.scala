#!/bin/sh
exec scala -J-Xmx2g -classpath ".:$GRAPHSLICES_JAR" "$0" "$@"
!#

import java.io.{File, PrintWriter}

import org.zviri.graphslices.{Graph, Edge, Vertex, Algorithms, IOUtil}
import org.joda.time.LocalDate
import org.joda.time.format.DateTimeFormat
import play.api.libs.json.{Json, OFormat}

case class NodeIsir(id: Long, stringId: String, name: String, personType: String, regionId: Option[Long], nodeType: String, date: Option[LocalDate])

case class EdgeIsir(srcId: Long, dstId: Long, edgeType: String, startDate: LocalDate, endDate: Option[LocalDate])

case class JsonLine(id: Long, pr: Seq[(Long, Double)], prEvolvingQuad: Seq[(Long, Double)], prEvolving: Seq[(Long, Double)])

object JsonLine {
  implicit def format: OFormat[JsonLine] = Json.format[JsonLine]
}

val dateFormat = DateTimeFormat.forPattern("yyyy-MM-dd")

val MAX_TIME = 4
val graph = Graph(Seq(
  Vertex(Seq(1), 1),
  Vertex(Seq(2), 1),
  Vertex(Seq(3), 1),
  Vertex(Seq(4), 1),
  Vertex(Seq(5), 1)
), Seq(
  Edge(Seq(1), Seq(1), Seq(2), 1),
  Edge(Seq(2), Seq(1), Seq(3), 1),
  Edge(Seq(3), Seq(2), Seq(4), 1),
  Edge(Seq(4), Seq(3), Seq(4), 1),
  Edge(Seq(5), Seq(1), Seq(5), 2),
  Edge(Seq(6), Seq(5), Seq(4), 3),
  Edge(Seq(7), Seq(1), Seq(4), 4)
)).pushDimension(
  e => (e.data to MAX_TIME).map(t => (t.toLong, 1.0)), keepAllNodes = true
)

println("Running PageRank algorithm...")
val graphPr = Algorithms.pagerank(
  graph, numIter = 100
).popDimension(
  vs => vs.map { case (topKey, key, pr) => (topKey, pr) }.sorted, es => Unit
)
val prMap = graphPr.vertices.map(v => (v.id.head, v.data)).toMap

println("Running evolving PageRank algorithm (1/(t*t))...")
val graphPrTimeQuad = Algorithms.evolvingPagerank(
  graph,
  timeDecayFunc = (time: Double) => 1.0 / (time * time),
  numIter = 100
)
val quadEvolvingPrMap = graphPrTimeQuad.vertices.map(v => (v.id.head, v.data)).toMap

println("Running evolving PageRank algorithm (1/t)...")
val graphPrTime = Algorithms.evolvingPagerank(
  graph,
  timeDecayFunc = (time: Double) => 1.0 / time,
  numIter = 100
)
val evolvingPrMap = graphPrTime.vertices.map(v => (v.id.head, v.data)).toMap


import JsonLine._

val jsonLines = prMap.keys.map(
  id => JsonLine(id, prMap(id), quadEvolvingPrMap(id), evolvingPrMap(id))
).map(line => Json.toJson(line))
IOUtil.saveJsonLine("./data/evolving_pr_small.jsonline", jsonLines)

#!/bin/sh
exec scala -J-Xmx2g -classpath ".:$GRAPHSLICES_JAR" "$0" "$@"
!#
import java.io.{File, PrintWriter}
import org.zviri.graphslices.{Algorithms, Edge, Graph, Vertex}
import scala.io.Source

case class NodeIsir(id: Long, stringId: String, name: String, nodeType: String)

case class EdgeIsir(sourceId: Long, targetId: Long, source: String, target: String, edgeType: String, year: Int)

val dataDir = sys.env("PHD_DATA_FOLDER") + "/networks_2.0"
val yearsRange: List[Int] = List.range(2008, 2016)
println("Loading nodes...")
val nodesIsir = yearsRange.flatMap {
  year =>
    val nodesIsir = Source.fromFile(
      s"$dataDir/nodes_Ústeckýkraj_$year.tsv"
    ).getLines().drop(1).map(
      row => row.split("\t", 4)
    ).map {
      case Array(id, nodeType, name, personType) => NodeIsir(id.hashCode, id, name, nodeType)
    }.toVector
    nodesIsir
}.distinct
println(s"Num nodes: ${nodesIsir.size}")

println("Loading edges...")
val nodesSet = nodesIsir.map(_.id).toSet
val edgesIsir = yearsRange.flatMap {
  year =>
    val edges = Source.fromFile(
      s"$dataDir/edges_Ústeckýkraj_$year.tsv"
    ).getLines().drop(1).map(
      row => row.trim.split("\t", 3)
    ).map {
      case Array(sourceId, targetId, edgeType) => EdgeIsir(sourceId.hashCode, targetId.hashCode, sourceId, targetId, edgeType, year)
    }.toVector
    edges
}.filter(
  e => nodesSet.contains(e.sourceId) && nodesSet.contains(e.targetId)
).groupBy(
  e => (e.sourceId, e.targetId)
).map {
  case (key, grp) => grp.head
}
println(s"Num edges: ${edgesIsir.size}")

val vertices = nodesIsir.map(n => Vertex(Seq(n.id), Unit)).toVector
val edges = edgesIsir.zipWithIndex.map {
  case (e, idx) => Edge(Seq(idx), Seq(e.sourceId), Seq(e.targetId), e.year)
}.toVector

val graph = Graph(vertices, edges)

println("Running LPA clustering algorithm...")
val start = System.currentTimeMillis

val clusteredGraph = Algorithms.clusterLPA(graph)
val runtime = (System.currentTimeMillis - start) / 1000.0

println(s"Clustering finished in ${runtime} seconds.")

println("Saving node data...")
val nodeWriter = new PrintWriter(new File(s"data/ustecky_lpaclusters_vertices.tsv"))
nodeWriter.println(List("id", "name", "node_type", "cluster").mkString("\t"))
clusteredGraph.outerJoinVertices(nodesIsir.map(n => (Seq(n.id), n))) {
  (cluster, vertexDataOpt) =>
    val vertexData = vertexDataOpt.get
    nodeWriter.println(Seq(vertexData.stringId, vertexData.name, vertexData.nodeType, cluster.data).mkString("\t"))
}
nodeWriter.close()

println("Saving edge data...")
val edgeWriter = new PrintWriter(new File(s"data/ustecky_lpaclusters_edges.tsv"))
edgeWriter.println(List("Source", "Target", "edgeType").mkString("\t"))
edgesIsir.foreach {
  edge => edgeWriter.println(Seq(edge.source, edge.target, edge.edgeType).mkString("\t"))
}
edgeWriter.close()

println("FINISHED!")
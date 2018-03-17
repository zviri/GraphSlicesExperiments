import java.io.{File, PrintWriter}

import org.zviri.graphslices.Algorithms.HitsScore
import org.zviri.graphslices.{Algorithms, Edge, Graph, Vertex}

import scala.io.Source

case class NodeIsir(id: Long, string_id: String, name: String, nodeType: String)

case class EdgeIsir(sourceId: Long, targetId: Long, source: String, target: String, edgeType: String, year: Int)

def calculate_ha_for_region(dataDir: String, yearsRange: List[Int], region: String): Unit = {
  println("\tLoading nodes...")
  val nodesIsir = yearsRange.flatMap {
    year =>
      val nodesIsir = Source.fromFile(
        s"$dataDir/nodes_${region}_$year.tsv"
      ).getLines().drop(1).map(
        row => row.split("\t", 4)
      ).map {
        case Array(id, nodeType, name, personType) => NodeIsir(id.hashCode, id, name, nodeType)
      }.toVector
      nodesIsir
  }.distinct

  println("\tLoading edges...")
  val nodesSet = nodesIsir.map(_.id).toSet
  val edgesIsir = yearsRange.flatMap {
    year =>
      val edges = Source.fromFile(
        s"$dataDir/edges_${region}_$year.tsv"
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

  val vertices = nodesIsir.map(n => Vertex(Seq(n.id), Unit)).toVector
  val edges = edgesIsir.zipWithIndex.map {
    case (e, idx) => Edge(Seq(idx), Seq(e.sourceId), Seq(e.targetId), e.year)
  }.toVector
  val graph = Graph(vertices, edges).pushDimension(e => Seq(e.data))

  println("\tRunning HITS algorithm...")
  val start = System.currentTimeMillis

  val graphHA = Algorithms.hits(
    graph, numIter = 100
  ).popDimension(vs => vs.map(v => (v._1, v._3)).toMap, es => Unit)
  val runtime = (System.currentTimeMillis - start) / 1000.0

  println(s"\tHITS finished in ${runtime} seconds.")


  val vertices_with_data = graphHA.outerJoinVertices(nodesIsir.map(n => (Seq(n.id), n))) {
    (vertex, n) => (vertex.data, n.get)
  }.vertices

  println("\tSaving results...")
  save_results(yearsRange, vertices_with_data, s"${region}_authorities.tsv", ha => ha.authority)
  save_results(yearsRange, vertices_with_data, s"${region}_hubs.tsv", ha => ha.hub)
  println("\tFINISHED!")
}

def save_results(yearsRange: List[Int],
                 vertices_with_data: Seq[Vertex[(Map[Long, HitsScore], NodeIsir)]],
                 file: String,
                 val_func: HitsScore => Double): Unit = {
  val writer = new PrintWriter(new File(s"data/${file}"))
  writer.println((List("string_id", "name", "node_type") ++ yearsRange).mkString("\t"))
  vertices_with_data.foreach(vertex => {
    val row = (List(vertex.data._2.string_id, vertex.data._2.name, vertex.data._2.nodeType) ++
      yearsRange.map {
        year => vertex.data._1.get(year) match {
          case Some(ha) => val_func(ha)
          case None => ""
        }
      }).mkString("\t")
    writer.println(row)
  })
  writer.close()
}

/// CALCULATE HITS SCORES FOR EACH REGION

val dataDir = sys.env("PHD_DATA_FOLDER") + "/networks_2.0"
val yearsRange: List[Int] = List.range(2008, 2016)
val regions = List(
  "jihočeskýkraj",
  "jihomoravskýkraj",
  "karlovarskýkraj",
  "krajvysočina",
  "královéhradeckýkraj",
  "libereckýkraj",
  "moravskoslezskýkraj",
  "olomouckýkraj",
  "pardubickýkraj",
  "plzeňskýkraj",
  "praha",
  "středočeskýkraj",
  "Ústeckýkraj",
  "zlínskýkraj"
)

regions.foreach {
  region =>
    println(s"Processing region: ${region}")
    calculate_ha_for_region(dataDir, yearsRange, region)
}

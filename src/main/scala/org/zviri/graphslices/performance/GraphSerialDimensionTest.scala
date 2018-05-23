package org.zviri.graphslices.performance

import org.scalameter.api._
import org.zviri.graphslices._

object GraphSerialDimensionTest extends CustomPerfTest("GraphSerialDimensionTest_") {
  val sizes = Gen.range("Complete Graph Size (nodes)")(10, 50, 10)

  val graphs = for {
    size <- sizes
  } yield {
    Generators.completeGraph(size).mapVertices(_ => 1.0).mapEdges(_ => 1.0)
  }

  val graphsWithDimension = for {
    size <- sizes
  } yield {
    val graph = Generators.completeGraph(size).mapVertices(_ => 1).mapEdges(_ => 1)
    graph.pushDimension(e => (0l to 10l).map(id => (id, e.data)))
  }

  performance of "SerialGraph" in {

    measure method "pushDimension" in {
      using(graphs) in {
        g => g.pushDimension(e => (0l until 10l).map(id => (id, e.data)))
      }
    }

    measure method "popDimension" in {
      using(graphsWithDimension) in {
        g => g.popDimension(
          vertices => vertices.map(_._3),
          edges => edges.map(_._3)
        )
      }
    }

    measure method "mapDimension" in {
      using(graphsWithDimension) in {
        g => g.mapDimension(g => g.mapVertices(v => v.data + 1))
      }
    }
  }
}

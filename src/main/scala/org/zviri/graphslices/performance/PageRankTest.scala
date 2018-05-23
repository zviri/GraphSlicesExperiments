package org.zviri.graphslices.performance

import org.scalameter.api._
import org.zviri.graphslices._

object PageRankTest extends CustomPerfTest("PageRankTest_") {

  val sizes = Gen.range("Complete Graph Size (nodes)")(10, 20, 10)

  val graphsSerial = for {
    size <- sizes
  } yield {
    Generators.completeGraph(size).mapVertices(_ => 1.0).mapEdges(_ => 1.0)
  }

  performance of "SerialGraph" in {
    measure method "pagerank" in {
      using(graphsSerial) in {
        g => Algorithms.pagerank(g.mapVertices(v => 1.0), numIter = 100)
      }
    }
  }

  val graphsParallel = for {
    size <- sizes
  } yield {
    Generators.completeGraph(size).mapVertices(_ => 1.0).mapEdges(_ => 1.0).par
  }

  performance of "ParallelGraph" in {
    measure method "pagerank" in {
      using(graphsParallel) in {
        g => Algorithms.pagerank(g, numIter = 100)
      }
    }
  }
}

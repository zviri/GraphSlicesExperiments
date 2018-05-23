package org.zviri.graphslices.performance

import org.scalameter.api._
import org.zviri.graphslices._

object PageRankParallelizationTest extends CustomPerfTest("PageRankParallelizationTest_") {

  val sizes = Gen.range("Complete Graph Size (nodes)")(10, 100, 10)

  val graphs = for {
    size <- sizes
  } yield {
    Generators.completeGraph(size).mapVertices(_ => 1.0).mapEdges(_ => 1.0).pushDimension(
      e => {
      val numDimensions: Long = 8l
      (0l to numDimensions).map(id => (id, e.data))
    }).par
  }

  performance of "ParallelGraph" in {
    measure method "pagerank_fullgraph" in {
      using(graphs) in {
        g => Algorithms.pagerank(g, numIter = 100)
      }
    }

    measure method "pagerank_mapDimension" in {
      using(graphs) in {
        g => g.mapDimension(graphDim => Algorithms.pagerank(graphDim, numIter = 100))
      }
    }
  }
}

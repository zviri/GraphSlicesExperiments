package org.zviri.graphslices.performance

import org.scalameter.api._
import org.zviri.graphslices.Generators

object GraphParallelOperationsTest extends CustomPerfTest("GraphParallelOperationsTest_") {
    val sizes = Gen.range("Complete Graph Size (nodes)")(100, 1500, 100)

    val graphs = for {
      size <- sizes
    } yield {
      Generators.completeGraph(size).mapVertices(_ => 1.0).mapEdges(_ => 1.0).par
    }

    performance of "GraphParallel" in {

      measure method "mapTriplets" in {
        using(graphs) in {
          g => g.mapTriplets(triplet => triplet.edge.data + 1)
        }
      }

      measure method "subgraph" in {
        using(graphs) in {
          g =>
            val numVertices = g.vertices.size
            g.subgraph(
              edgeTriplet => edgeTriplet.edge.id.head % 2 == 0,
              vertex => vertex.id.head < numVertices / 2
            )
        }
      }

      measure method "aggregateNeighbors" in {
        using(graphs) in {
          g => g.aggregateNeighbors[Double](
            edgeCtx => Seq(edgeCtx.msgToDst(edgeCtx.srcVertex.data)),
            _ + _
          )
        }
      }
    }
  }

package org.zviri.graphslices.performance

import org.scalameter.api._
import org.zviri.graphslices.Generators

object GraphSerialOperationsTest extends CustomPerfTest("GraphSerialOperationsTest_") {

    val sizes = Gen.range("Complete Graph Size (nodes)")(100, 1500, 100)

    val graphs = for {
      size <- sizes
    } yield {
      Generators.completeGraph(size).mapVertices(_ => 1.0).mapEdges(_ => 1.0)
    }

    performance of "Graph" in {
      measure method "mapVertices" in {
        using(graphs) in {
          g => g.mapVertices(v => v.data + 1)
        }
      }

      measure method "mapEdges" in {
        using(graphs) in {
          g => g.mapEdges(e => e.data + 1)
        }
      }

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

      measure method "outerJoinVertices" in {
        using(graphs) in {
          g => g.outerJoinVertices(g.vertices.map(v => (v.id, v.data))) {
            (vertex, data) => vertex.data + data.get
          }
        }
      }

      measure method "reverseEdges" in {
        using(graphs) in {
          g => g.reverseEdges()
        }
      }
    }
  }

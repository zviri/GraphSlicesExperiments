package org.zviri.graphslices.performance

import org.scalameter.api._
import org.zviri.graphslices._

object MultiIndexTest extends CustomPerfTest("MultiIndexTest_") {

  val sizes = Gen.range("IndexSize")(100000, 1000000, 100000)

  val multiIndexesRecursive = for {
    size <- sizes
  } yield {
    val keys = (0l until size).map(k => Seq(k % 5, k  % 10, k)).toVector
    val values = (0 until size).toVector
    RecursiveMultiIndex(keys, values)
  }

  performance of "RecursiveMultiIndex" in {
    measure method "access" in {
      using(multiIndexesRecursive) in {
        m => m.apply(1)(1)(1)
      }
    }

    measure method "flatten" in {
      using(multiIndexesRecursive) in {
        m => m.flatten
      }
    }
  }

  val multiIndexesFlat = for {
    size <- sizes
  } yield {
    val keys = (0l until size).map(k => Seq(k % 5, k  % 10, k)).toVector
    val values = (0 until size).toVector
    FlatMultiIndex(keys, values)
  }

  performance of "FlatMultiIndex" in {
    measure method "access" in {
      using(multiIndexesFlat) in {
        m => m.apply(1)(1)(1)
      }
    }
  }

  measure method "flatten" in {
    using(multiIndexesFlat) in {
      m => m.flatten
    }
  }
}

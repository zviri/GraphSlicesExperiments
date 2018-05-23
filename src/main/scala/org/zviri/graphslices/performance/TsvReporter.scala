package org.zviri.graphslices.performance

import java.io.{File, FileWriter, PrintWriter}

import org.scalameter.{Context, _}
import org.scalameter.utils.Tree


case class TsvReporter[T](prefix: String) extends Reporter[T] {

  val sep = File.separator

  def report(result: CurveData[T], persistor: Persistor): Unit = {

    val resultDir = currentContext(Key.reports.resultDir)
    new File(s"$resultDir").mkdirs()

    val fileName = s"$resultDir$sep$prefix${result.context.scope}.tsv"

    var writer: PrintWriter = null

    try {
      writer = new PrintWriter(new FileWriter(fileName, false))
      writer.println("data_size\truntime\tunit")
      result.measurements.foreach{
        measurement => writer.println(s"${measurement.params.axisData.head._2}\t${measurement.value}\t${measurement.units}")
      }
    } finally {
      if (writer != null) writer.close()
    }
  }

  def report(result: Tree[CurveData[T]], persistor: Persistor) = true
}
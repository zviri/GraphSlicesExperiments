package org.zviri.graphslices.performance

import org.scalameter.Reporter.Composite
import org.scalameter.api._

class CustomPerfTest(prefix: String) extends Bench.ForkedTime {

  override lazy val reporter = Composite(new LoggingReporter, new TsvReporter(prefix))

  override def defaultConfig: Context = Context(
    exec.benchRuns -> 10,
    exec.minWarmupRuns -> 10,
    exec.maxWarmupRuns -> 10,
    exec.independentSamples -> 1,
    exec.jvmflags -> List("-Xms2g", "-Xmx16g"),
    verbose -> true,
    reports.resultDir -> "./perf"
  )

}

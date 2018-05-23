
lazy val root = (project in file(".")).
  settings(
    name := "GraphSlicesExperiments",
    organization := "org.zviri.graphslices",
    version := "1.0",
    scalaVersion := "2.12.4"
  )

resolvers += "Local Maven Repository" at "file://"+Path.userHome.absolutePath+"/.m2/repository"

libraryDependencies ++= Seq(
  "com.storm-enroute" %% "scalameter" % "0.10",
  "org.zviri.graphslices" %% "graphslices" % "1.0"
)

assemblyMergeStrategy in assembly <<= (mergeStrategy in assembly) {
  (old) => {
    case PathList("META-INF", xs@_*) => MergeStrategy.discard
    case x => MergeStrategy.first
  }
}

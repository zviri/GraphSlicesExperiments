#!/usr/bin/env bash
set -x

GRAPH_SLICES_JAR=$1

java -cp $GRAPH_SLICES_JAR org.zviri.graphslices.performance.GraphParallelOperationsTest | tee ./data/perf/GraphParallelOperationsTest.log
java -cp $GRAPH_SLICES_JAR org.zviri.graphslices.performance.GraphSerialOperationsTest | tee ./data/perf/GraphSerialOperationsTest.log
java -cp $GRAPH_SLICES_JAR org.zviri.graphslices.performance.GraphSerialDimensionTest | tee ./data/perf/GraphSerialDimensionTest.log
java -cp $GRAPH_SLICES_JAR org.zviri.graphslices.performance.MultiIndexTest | tee ./data/perf/MultiIndexTest.log
java -cp $GRAPH_SLICES_JAR org.zviri.graphslices.performance.PageRankParallelizationTest | tee ./data/perf/PageRankParallelizationTest.log
java -cp $GRAPH_SLICES_JAR org.zviri.graphslices.performance.PageRankTest | tee ./data/perf/PageRankTest.log

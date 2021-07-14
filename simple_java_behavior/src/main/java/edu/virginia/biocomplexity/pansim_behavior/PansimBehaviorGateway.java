/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import com.opencsv.exceptions.CsvException;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.arrow.memory.RootAllocator;
import py4j.GatewayServer;

/**
 *
 * @author parantapa
 */
public class PansimBehaviorGateway {
    public static GatewayServer gatewayServer;
    
    public long seed;
    public int num_ticks;
    public int max_visits;
    
    public ArrayList<String> attr_names;
    
    public String start_state_file;
    public ArrayList<String> visit_files;
    
    public RootAllocator allocator;
    public StateDataFrameBuilder start_state_df;
    public TickVisitReader visit_reader;
    
    public int next_tick;
    public byte[] next_state_df_raw;
    public byte[] next_visit_df_raw;
    
    PansimBehaviorGateway () throws IOException, FileNotFoundException, CsvException {
        seed = Long.parseLong(System.getenv("SEED"));
        num_ticks = Integer.parseInt(System.getenv("NUM_TICKS"));
        max_visits = Integer.parseInt(System.getenv("MAX_VISITS"));
        
        String[] attrs_sa = System.getenv("VISUAL_ATTRIBUTES").split(",");
        attr_names = new ArrayList<>(Arrays.asList(attrs_sa));
        for (String name: attr_names) {
            System.out.printf("Attibute: %s\n", name);
        }
        
        start_state_file = System.getenv("START_STATE_FILE");
        visit_files = new ArrayList<>();
        for (int i=0; i < num_ticks; i++) {
            String file = System.getenv(String.format("VISIT_FILE_%d", i));
            visit_files.add(file);
            System.out.printf("Visit file %d: %s\n", i, file);
        }
        
        allocator = new RootAllocator(Long.MAX_VALUE);

        start_state_df = StartStateReader.readStartState(start_state_file, allocator, seed);
        System.out.printf("Start state has %d rows\n", start_state_df.schemaRoot.getRowCount());
        
        visit_reader = new TickVisitReader(visit_files, attr_names, num_ticks, max_visits);
        
        next_tick = 0;
        next_state_df_raw = start_state_df.toBytes();
        
        VisitDataFrameBuilder next_visit_df = visit_reader.getVisits(0, start_state_df, allocator);
        System.out.printf("Next visit dataframe has %d rows\n", next_visit_df.schemaRoot.getRowCount());
        next_visit_df_raw = next_visit_df.toBytes();
    }
    
    public void runBehaviorModel(byte[] cur_state_df_raw, byte[] visit_output_df_raw) throws IOException, FileNotFoundException, CsvException {
        StateDataFrameReader cur_state_df = new StateDataFrameReader(cur_state_df_raw, allocator);
        VisitOutputDataFrameReader visit_output_df = new VisitOutputDataFrameReader(attr_names, visit_output_df_raw, allocator);
        
        System.out.printf("Recived new state dataframe with %d rows\n", cur_state_df.schemaRoot.getRowCount());
        System.out.printf("Recived new visit output dataframe with %d rows\n", visit_output_df.schemaRoot.getRowCount());
        
        next_tick++;
        
        if (next_tick < num_ticks) {
            next_state_df_raw = cur_state_df_raw;
        
            VisitDataFrameBuilder next_visit_df = visit_reader.getVisits(next_tick, start_state_df, allocator);
            System.out.printf("Next visit dataframe has %d rows\n", next_visit_df.schemaRoot.getRowCount());

            next_visit_df_raw = next_visit_df.toBytes();
        } else {
            next_state_df_raw = null;
            next_visit_df_raw = null;
        }
    }
    
    public byte[] getNextStateDataFrame() {
        System.out.printf("Returning state dataframe for tick %d\n", next_tick);
        return next_state_df_raw;
    }
    
    public byte[] getNextVisitDataFrame() {
        System.out.printf("Returning next visit dataframe for tick %d\n", next_tick);
        return next_visit_df_raw;
    }
    
    public void cleanup() {
        System.out.println("Preparing Pansim Behavior Server for Shutdown");
    }
    
    public static void main(String[] args) throws IOException, FileNotFoundException, CsvException {
        gatewayServer = new GatewayServer(new PansimBehaviorGateway());
        gatewayServer.start();
        System.out.println("Pansim Behavior Server Started");
        
        // var g = new SanityCheckTests();
        // g.testStateDataFrame();
        // g.testVisitDataFrame();
        // g.testVisitOutputDataFrame();
        // g.testReplayBehaviorModel();
    }
}

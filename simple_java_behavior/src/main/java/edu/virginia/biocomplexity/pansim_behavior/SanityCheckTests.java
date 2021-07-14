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
import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.arrow.memory.RootAllocator;

/**
 *
 * @author parantapa
 */
public class SanityCheckTests {
    public void testStateDataFrame() {
        RootAllocator allocator = new RootAllocator(Long.MAX_VALUE);

        StateDataFrameBuilder builder = new StateDataFrameBuilder(100000, allocator);
        builder.reset();
        for (int i = 0; i < 100 ; i++) {
            builder.pid.set(i, i);
            builder.group.set(i, 0);
            builder.current_state.set(i, 0);
            builder.next_state.set(i, -1);
            builder.dwell_time.set(i, -1);
            builder.seed.set(i, i);
        }
        builder.setValueCount(100);
        
        byte[] raw;
        try {
            raw = builder.toBytes();
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println(raw.length);
        
        StateDataFrameReader reader;
        try {
            reader = new StateDataFrameReader(raw, allocator);
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println(reader.schemaRoot.getRowCount());
        System.out.println(reader.schemaRoot.contentToTSVString());
    }
    
    public void testVisitDataFrame() {
        RootAllocator allocator = new RootAllocator(Long.MAX_VALUE);
        
        ArrayList<String> attr_names = new ArrayList<>();
        attr_names.add("attr_1");
        attr_names.add("attr_2");
        attr_names.add("attr_3");

        VisitDataFrameBuilder builder = new VisitDataFrameBuilder(attr_names, 1000000, allocator);
        builder.reset();
        for (int i = 0; i < 100 ; i++) {
            builder.lid.set(i, i);
            builder.pid.set(i, i);
            builder.group.set(i, 0);
            builder.state.set(i, 0);
            builder.behavior.set(i, i % 2);
            builder.start_time.set(i, i);
            builder.end_time.set(i, i + 100);
            for (String attr: attr_names) {
                builder.attrs.get(attr).set(i, 0);
            }
        }
        builder.setValueCount(100);
        
        byte[] raw;
        try {
            raw = builder.toBytes();
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println(raw.length);
        
        VisitDataFrameReader reader;
        try {
            reader = new VisitDataFrameReader(attr_names, raw, allocator);
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println(reader.schemaRoot.getRowCount());
        System.out.println(reader.schemaRoot.contentToTSVString());
    }
    
    public void testVisitOutputDataFrame() {
        RootAllocator allocator = new RootAllocator(Long.MAX_VALUE);
        
        ArrayList<String> attr_names = new ArrayList<>();
        attr_names.add("attr_1");
        attr_names.add("attr_2");
        attr_names.add("attr_3");

        VisitOutputDataFrameBuilder builder = new VisitOutputDataFrameBuilder(attr_names, 1000000, allocator);
        for (int i = 0; i < 100 ; i++) {
            builder.lid.set(i, i);
            builder.pid.set(i, i);
            builder.inf_prob.set(i, 1.0 / i);
            builder.n_contacts.set(i, i);
            for (String attr: attr_names) {
                builder.attrs.get(attr).set(i, 42);
            }
        }
        builder.setValueCount(100);
        
        byte[] raw;
        try {
            raw = builder.toBytes();
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println(raw.length);
        
        VisitOutputDataFrameReader reader;
        try {
            reader = new VisitOutputDataFrameReader(attr_names, raw, allocator);
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println(reader.schemaRoot.getRowCount());
        System.out.println(reader.schemaRoot.contentToTSVString());
    }
    
    public void testReplayBehaviorModel() {
        RootAllocator allocator = new RootAllocator(Long.MAX_VALUE);
        String start_state_file = "/home/parantapa/start.csv";
        long seed = 42;
        
        StateDataFrameBuilder state_df;
        try {
            state_df = StartStateReader.readStartState(start_state_file, allocator, seed);
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        } catch (CsvException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println("Start state dataframe");
        System.out.println(state_df.schemaRoot.getRowCount());
        System.out.println(state_df.schemaRoot.contentToTSVString());
        
        ArrayList<String> visit_files = new ArrayList<String>();
        visit_files.add("/home/parantapa/visits.csv");
        
        ArrayList<String> attr_names = new ArrayList<>();
        attr_names.add("attr_1");
        attr_names.add("attr_2");
        attr_names.add("attr_3");
        
        TickVisitReader visit_reader = new TickVisitReader(visit_files, attr_names, 1, 100);
        VisitDataFrameBuilder visit_df;
        try {
            visit_df = visit_reader.getVisits(0, state_df, allocator);
        } catch (IOException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        } catch (CsvException ex) {
            Logger.getLogger(PansimBehaviorGateway.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        System.out.println("Tick 0 visit dataframe");
        System.out.println(visit_df.schemaRoot.getRowCount());
        System.out.println(visit_df.schemaRoot.contentToTSVString());
    }
}

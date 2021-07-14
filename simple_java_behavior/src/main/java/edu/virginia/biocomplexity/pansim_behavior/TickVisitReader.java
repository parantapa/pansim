/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvException;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.apache.arrow.memory.BufferAllocator;

/**
 *
 * @author parantapa
 */
public class TickVisitReader {
    public ArrayList<String> visit_files;
    public ArrayList<String> attr_names;
    public int sim_ticks;
    public int max_visits;
    
    TickVisitReader(ArrayList<String> visit_files, ArrayList<String> attr_names, int sim_ticks, int max_visits) {
        this.visit_files = visit_files;
        this.attr_names = attr_names;
        this.sim_ticks = sim_ticks;
        this.max_visits = max_visits;
    }
    
    public VisitDataFrameBuilder getVisits(int tick, StateDataFrame state_df, BufferAllocator allocator) throws FileNotFoundException, IOException, CsvException {
        FileReader filereader = new FileReader(visit_files.get(tick));
        CSVReader csvReader = new CSVReader(filereader);
        List<String[]> lines = csvReader.readAll();
        
        HashMap<Long,Integer> pid_i = new HashMap<>();
        for (int i=0; i < state_df.schemaRoot.getRowCount(); i++) {
            long pid = state_df.pid.get(i);
            pid_i.put(pid, i);
        }
        
        VisitDataFrameBuilder builder = new VisitDataFrameBuilder(attr_names, max_visits, allocator);
        for (int i=1; i < lines.size(); i++) {
            String[] line = lines.get(i);
            long pid = Long.parseLong(line[0]);
            long lid = Long.parseLong(line[1]);
            int start_time = Integer.parseInt(line[2]);
            int end_time = Integer.parseInt(line[3]);
            int group = state_df.group.get(pid_i.get(pid));
            int state = state_df.current_state.get(pid_i.get(pid));
            int behavior = 0;
            
            builder.lid.set(i-1, lid);
            builder.pid.set(i-1, pid);
            builder.group.set(i-1, group);
            builder.state.set(i-1, state);
            builder.behavior.set(i-1, behavior);
            builder.start_time.set(i-1, start_time);
            builder.end_time.set(i-1, end_time);
            for (String name: attr_names) {
                builder.attrs.get(name).set(i-1, 0);
            }
        }
        builder.setValueCount(lines.size() -1);
        
        return builder;
    }
}

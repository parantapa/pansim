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
import java.util.List;
import java.util.Random;
import org.apache.arrow.memory.BufferAllocator;

/**
 * @author parantapa
 */
public class StartStateReader {
   
    public static StateDataFrameBuilder readStartState(String state_file, BufferAllocator allocator, long seed) throws FileNotFoundException, IOException, CsvException {
        FileReader filereader = new FileReader(state_file);
        CSVReader csvReader = new CSVReader(filereader);
        List<String[]> lines = csvReader.readAll();
        
        Random random = new Random(seed);
        
        StateDataFrameBuilder builder = new StateDataFrameBuilder(lines.size()-1, allocator);
        for (int i=1; i < lines.size(); i++) {
            String[] line = lines.get(i);
            long pid = Long.parseLong(line[0]);
            int group = Integer.parseInt(line[1]);
            int current_state = Integer.parseInt(line[2]);

            builder.pid.set(i-1, pid);
            builder.group.set(i-1, group);
            builder.current_state.set(i-1, current_state);
            builder.next_state.set(i-1, -1);
            builder.dwell_time.set(i-1, -1);
            builder.seed.set(i-1, random.nextLong());
        }
        builder.setValueCount(lines.size() -1);
        
        return builder;
    }
}

/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.channels.Channels;
import java.util.Arrays;
import java.util.List;
import org.apache.arrow.memory.BufferAllocator;
import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.FieldVector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.TinyIntVector;
import org.apache.arrow.vector.VectorSchemaRoot;
import org.apache.arrow.vector.ipc.ArrowFileWriter;
import org.apache.arrow.vector.types.pojo.Field;

/**
 *
 * @author parantapa
 */
public class StateDataFrameBuilder extends StateDataFrame {
    public StateDataFrameBuilder(int max_rows, BufferAllocator allocator) {
        pid = new BigIntVector("pid", allocator);
        group = new TinyIntVector("group", allocator);
        current_state = new TinyIntVector("current_state", allocator);
        next_state = new TinyIntVector("next_state", allocator);
        dwell_time = new IntVector("dwell_time", allocator);
        seed = new BigIntVector("seed", allocator);
        
        pid.allocateNew(max_rows);
        group.allocateNew(max_rows);
        current_state.allocateNew(max_rows);
        next_state.allocateNew(max_rows);
        dwell_time.allocateNew(max_rows);
        seed.allocateNew(max_rows);        
        
        List<Field> fields = Arrays.asList(
            pid.getField(),
            group.getField(),
            current_state.getField(),
            next_state.getField(),
            dwell_time.getField(),
            seed.getField()
        );

        List<FieldVector> vectors = Arrays.asList(
            pid,
            group,
            current_state,
            next_state,
            dwell_time,
            seed
        );

        schemaRoot = new VectorSchemaRoot(fields, vectors);
    }
    
    public void setValueCount(int count) {
        pid.setValueCount(count);
        group.setValueCount(count);
        current_state.setValueCount(count);
        next_state.setValueCount(count);
        dwell_time.setValueCount(count);
        seed.setValueCount(count);
        schemaRoot.setRowCount(count);
    }
    
    public void reset() {
        pid.reset();
        group.reset();
        current_state.reset();
        next_state.reset();
        dwell_time.reset();
        seed.reset();
    }
    
    public void close() {
        pid.close();
        group.close();
        current_state.close();
        next_state.close();
        dwell_time.close();
        seed.close();
    }
    
    public byte[] toBytes() throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ArrowFileWriter writer = new ArrowFileWriter(schemaRoot, null, Channels.newChannel(out));
        
        writer.start();
        writer.writeBatch();
        writer.end();
        
        writer.close();
        byte[] outb = out.toByteArray();
        out.close();
        
        return outb;
    }
}

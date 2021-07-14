package edu.virginia.biocomplexity.pansim_behavior;


import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.channels.Channels;
import java.util.ArrayList;
import java.util.HashMap;
import org.apache.arrow.memory.BufferAllocator;
import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.FieldVector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.TinyIntVector;
import org.apache.arrow.vector.VectorSchemaRoot;
import org.apache.arrow.vector.ipc.ArrowFileWriter;
import org.apache.arrow.vector.types.pojo.Field;

/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/**
 *
 * @author parantapa
 */
public class VisitDataFrameBuilder extends VisitDataFrame {
    
    VisitDataFrameBuilder(ArrayList<String> attr_names, int max_rows, BufferAllocator allocator) {
        lid = new BigIntVector("lid", allocator);
        pid = new BigIntVector("pid", allocator);
        group = new TinyIntVector("group", allocator);
        state = new TinyIntVector("state", allocator);
        behavior = new TinyIntVector("behavior", allocator);
        start_time = new IntVector("start_time", allocator);
        end_time = new IntVector("end_time", allocator);
        attrs = new HashMap<>();
        
        for (int i=0; i < attr_names.size(); i++) {
            attrs.put(attr_names.get(i), new TinyIntVector(attr_names.get(i), allocator));
        }
        
        lid.allocateNew(max_rows);
        pid.allocateNew(max_rows);
        group.allocateNew(max_rows);
        state.allocateNew(max_rows);
        behavior.allocateNew(max_rows);
        start_time.allocateNew(max_rows);
        end_time.allocateNew(max_rows);
        for (String name: attrs.keySet()) {
            attrs.get(name).allocateNew(max_rows);
        }
        
        ArrayList<Field> fields = new ArrayList<>();
        fields.add(lid.getField());
        fields.add(pid.getField());
        fields.add(group.getField());
        fields.add(state.getField());
        fields.add(behavior.getField());
        fields.add(start_time.getField());
        fields.add(end_time.getField());
        for (String name: attrs.keySet()) {
            fields.add(attrs.get(name).getField());
        }
        
        ArrayList<FieldVector> vectors = new ArrayList<>();
        vectors.add(lid);
        vectors.add(pid);
        vectors.add(group);
        vectors.add(state);
        vectors.add(behavior);
        vectors.add(start_time);
        vectors.add(end_time);
        for (String name: attrs.keySet()) {
            vectors.add(attrs.get(name));
        }
        
        schemaRoot = new VectorSchemaRoot(fields, vectors);
    }
    
    public void setValueCount(int count) {
        lid.setValueCount(count);
        pid.setValueCount(count);
        group.setValueCount(count);
        state.setValueCount(count);
        behavior.setValueCount(count);
        start_time.setValueCount(count);
        end_time.setValueCount(count);
        for (String name: attrs.keySet()) {
            attrs.get(name).setValueCount(count);
        }
        schemaRoot.setRowCount(count);
    }
    
    public void reset() {
        lid.reset();
        pid.reset();
        group.reset();
        state.reset();
        behavior.reset();
        start_time.reset();
        end_time.reset();
        for (String name: attrs.keySet()) {
            attrs.get(name).reset();
        }
    }
    
    public void close() {
        lid.close();
        pid.close();
        group.close();
        state.close();
        behavior.close();
        start_time.close();
        end_time.close();
        for (String name: attrs.keySet()) {
            attrs.get(name).close();
        }

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

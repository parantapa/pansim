/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.channels.Channels;
import java.util.ArrayList;
import java.util.HashMap;
import org.apache.arrow.memory.BufferAllocator;
import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.FieldVector;
import org.apache.arrow.vector.Float8Vector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.VectorSchemaRoot;
import org.apache.arrow.vector.ipc.ArrowFileWriter;
import org.apache.arrow.vector.types.pojo.Field;

/**
 *
 * @author parantapa
 */
public class VisitOutputDataFrameBuilder extends VisitOutputDataFrame {
    
    VisitOutputDataFrameBuilder(ArrayList<String> attr_names, int max_rows, BufferAllocator allocator) {
        lid = new BigIntVector("lid", allocator);
        pid = new BigIntVector("pid", allocator);
        inf_prob = new Float8Vector("inf_prob", allocator);
        n_contacts = new IntVector("n_contacts", allocator);
        attrs = new HashMap<>();
        for (String name: attr_names) {
            attrs.put(name, new IntVector(name, allocator));
        }
        
        lid.allocateNew(max_rows);
        pid.allocateNew(max_rows);
        inf_prob.allocateNew(max_rows);
        n_contacts.allocateNew(max_rows);
        for (String name: attrs.keySet()) {
            attrs.get(name).allocateNew(max_rows);
        }
        
        ArrayList<Field> fields = new ArrayList<>();
        fields.add(lid.getField());
        fields.add(pid.getField());
        fields.add(inf_prob.getField());
        fields.add(n_contacts.getField());
        for (String name: attrs.keySet()) {
            fields.add(attrs.get(name).getField());
        }
        
        ArrayList<FieldVector> vectors = new ArrayList<>();
        vectors.add(lid);
        vectors.add(pid);
        vectors.add(inf_prob);
        vectors.add(n_contacts);
        for (String name: attrs.keySet()) {
            vectors.add(attrs.get(name));
        }
        
        schemaRoot = new VectorSchemaRoot(fields, vectors);
    }
    
    public void setValueCount(int count) {
        lid.setValueCount(count);
        pid.setValueCount(count);
        inf_prob.setValueCount(count);
        n_contacts.setValueCount(count);
        for (String name: attrs.keySet()) {
            attrs.get(name).setValueCount(count);
        }
        schemaRoot.setRowCount(count);
    }
    
    public void reset() {
        lid.reset();
        pid.reset();
        inf_prob.reset();
        n_contacts.reset();
        for (String name: attrs.keySet()) {
            attrs.get(name).reset();
        }
    }
    
    public void close() {
        lid.close();
        pid.close();
        inf_prob.close();
        n_contacts.close();
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

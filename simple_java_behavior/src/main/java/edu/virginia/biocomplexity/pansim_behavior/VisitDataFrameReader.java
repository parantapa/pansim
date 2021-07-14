/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import org.apache.arrow.memory.BufferAllocator;
import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.TinyIntVector;
import org.apache.arrow.vector.ipc.ArrowFileReader;
import org.apache.arrow.vector.ipc.message.ArrowBlock;
import org.apache.arrow.vector.util.ByteArrayReadableSeekableByteChannel;

/**
 *
 * @author parantapa
 */
public class VisitDataFrameReader extends VisitDataFrame {
    
    VisitDataFrameReader(ArrayList<String> attr_names, byte[] inb, BufferAllocator allocator) throws IOException {
        ByteArrayReadableSeekableByteChannel in = new ByteArrayReadableSeekableByteChannel(inb);
        ArrowFileReader reader = new ArrowFileReader(in, allocator);
        
        ArrowBlock block = reader.getRecordBlocks().get(0);
        reader.loadRecordBatch(block);
        schemaRoot = reader.getVectorSchemaRoot();
        
        lid = (BigIntVector) schemaRoot.getVector("lid");
        pid = (BigIntVector) schemaRoot.getVector("pid");
        group = (TinyIntVector) schemaRoot.getVector("group");
        state = (TinyIntVector) schemaRoot.getVector("state");
        behavior = (TinyIntVector) schemaRoot.getVector("behavior");
        start_time = (IntVector) schemaRoot.getVector("start_time");
        end_time = (IntVector) schemaRoot.getVector("end_time");
        
        attrs = new HashMap<>();
        for (String name: attr_names) {
            TinyIntVector vector = (TinyIntVector) schemaRoot.getVector(name);
            attrs.put(name, vector);
        }
    }
}
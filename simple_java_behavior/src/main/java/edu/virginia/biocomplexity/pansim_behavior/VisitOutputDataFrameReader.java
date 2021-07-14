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
import org.apache.arrow.vector.Float8Vector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.ipc.ArrowFileReader;
import org.apache.arrow.vector.ipc.message.ArrowBlock;
import org.apache.arrow.vector.util.ByteArrayReadableSeekableByteChannel;

/**
 *
 * @author parantapa
 */
public class VisitOutputDataFrameReader extends VisitOutputDataFrame {
    
    VisitOutputDataFrameReader(ArrayList<String> attr_names, byte[] inb, BufferAllocator allocator) throws IOException {
        ByteArrayReadableSeekableByteChannel in = new ByteArrayReadableSeekableByteChannel(inb);
        ArrowFileReader reader = new ArrowFileReader(in, allocator);
        
        ArrowBlock block = reader.getRecordBlocks().get(0);
        reader.loadRecordBatch(block);
        schemaRoot = reader.getVectorSchemaRoot();
        
        lid = (BigIntVector) schemaRoot.getVector("lid");
        pid = (BigIntVector) schemaRoot.getVector("pid");
        inf_prob = (Float8Vector) schemaRoot.getVector("inf_prob");
        n_contacts = (IntVector) schemaRoot.getVector("n_contacts");

        attrs = new HashMap<>();
        for (String name: attr_names) {
            IntVector vector = (IntVector) schemaRoot.getVector(name);
            attrs.put(name, vector);
        }
    }
}

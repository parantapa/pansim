/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import java.io.IOException;
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
public class StateDataFrameReader extends StateDataFrame {
    StateDataFrameReader(byte[] inb, BufferAllocator allocator) throws IOException {
        ByteArrayReadableSeekableByteChannel in = new ByteArrayReadableSeekableByteChannel(inb);
        ArrowFileReader reader = new ArrowFileReader(in, allocator);
        
        ArrowBlock block = reader.getRecordBlocks().get(0);
        reader.loadRecordBatch(block);
        schemaRoot = reader.getVectorSchemaRoot();
        
        pid = (BigIntVector) schemaRoot.getVector("pid");
        group = (TinyIntVector) schemaRoot.getVector("group");
        current_state = (TinyIntVector) schemaRoot.getVector("current_state");
        next_state = (TinyIntVector) schemaRoot.getVector("next_state");
        dwell_time = (IntVector) schemaRoot.getVector("dwell_time");
        seed = (BigIntVector) schemaRoot.getVector("seed");
    }
}

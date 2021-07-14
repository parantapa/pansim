/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.TinyIntVector;
import org.apache.arrow.vector.VectorSchemaRoot;

/**
 *
 * @author parantapa
 */
public class StateDataFrame {
    public BigIntVector pid;
    public TinyIntVector group;
    public TinyIntVector current_state;
    public TinyIntVector next_state;
    public IntVector dwell_time;
    public BigIntVector seed;
    
    public VectorSchemaRoot schemaRoot;
}

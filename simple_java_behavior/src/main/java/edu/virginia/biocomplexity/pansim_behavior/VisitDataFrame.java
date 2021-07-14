/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import java.util.HashMap;
import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.TinyIntVector;
import org.apache.arrow.vector.VectorSchemaRoot;

/**
 *
 * @author parantapa
 */
public class VisitDataFrame {
    public BigIntVector lid;
    public BigIntVector pid;
    public TinyIntVector group;
    public TinyIntVector state;
    public TinyIntVector behavior;
    public IntVector start_time;
    public IntVector end_time;
    public HashMap<String, TinyIntVector> attrs;
    
    public VectorSchemaRoot schemaRoot;
}

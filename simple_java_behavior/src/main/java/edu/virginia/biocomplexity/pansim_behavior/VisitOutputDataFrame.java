/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package edu.virginia.biocomplexity.pansim_behavior;

import java.util.HashMap;
import org.apache.arrow.vector.BigIntVector;
import org.apache.arrow.vector.Float8Vector;
import org.apache.arrow.vector.IntVector;
import org.apache.arrow.vector.VectorSchemaRoot;

/**
 *
 * @author parantapa
 */
public class VisitOutputDataFrame {
    public BigIntVector lid;
    public BigIntVector pid;
    public Float8Vector inf_prob;
    public IntVector n_contacts;
    public HashMap<String, IntVector> attrs;
    
    public VectorSchemaRoot schemaRoot;
}

"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export function InsightDetailPanel() {
    // Stub for detailed insight view showing the narrative
    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Business Narrative Viewer</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">What Happened</h4>
                        <p className="text-sm leading-relaxed">
                            Analytics indicates a significant pattern in the Sales domain, specifically a 14% drop in Q3 EMEA revenues compared to Q2.
                        </p>
                    </div>
                    
                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">Why It Happened</h4>
                        <p className="text-sm leading-relaxed">
                            Contributing factors derived from evidence objects show strong correlation with supply chain disruptions in the region starting mid-July.
                        </p>
                    </div>

                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">Business Impact</h4>
                        <p className="text-sm leading-relaxed">
                            This could affect overall annual metrics by up to 15% if left unresolved. Score: 92/100.
                        </p>
                    </div>

                    <div>
                        <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">Evidence & Validation</h4>
                        <div className="bg-slate-100 p-3 rounded-md text-xs font-mono text-slate-800">
                            - ContextRef: ctxt-8f92a1<br/>
                            - EvidenceRef: evd-2910bb<br/>
                            - Validated: True (No Hallucinations Detected)
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

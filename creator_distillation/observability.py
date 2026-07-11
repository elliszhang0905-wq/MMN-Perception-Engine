import os
import time
from contextlib import contextmanager

try:
    from langfuse import Langfuse
except ImportError:
    Langfuse = None


class ModelObserver:
    def __init__(self):
        self.client = Langfuse() if Langfuse and os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY") else None

    @contextmanager
    def generation(self, task_id, stage, model, evidence, prompt_version=None):
        started=time.monotonic(); generation=None
        safe_evidence=[{"evidenceId":x.get("id"),"type":x.get("evidence_type"),"confidence":x.get("confidence")} for x in (evidence or [])]
        if self.client:
            trace=self.client.trace(name="creator-distillation",id=task_id,metadata={"stage":stage})
            generation=trace.generation(name=stage,model=model,input={"promptVersion":prompt_version or os.getenv("MMN_CREATOR_PROMPT_VERSION","creator-dna-v1"),"evidence":safe_evidence})
        result={"output":None,"cost":None,"humanCorrection":None}
        try:
            yield result
            if generation: generation.end(output=result["output"],metadata={"elapsedMs":round((time.monotonic()-started)*1000),"cost":result["cost"],"humanCorrection":result["humanCorrection"]})
        except Exception as exc:
            if generation: generation.end(level="ERROR",status_message=str(exc))
            raise


observer=ModelObserver()

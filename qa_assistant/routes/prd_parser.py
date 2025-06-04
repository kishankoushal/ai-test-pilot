from fastapi import APIRouter, Query
from services import confluence_fetcher, doc_parser, feature_extractor, testplan_generator, testcase_generator

router = APIRouter()

@router.get("/parse_prd/")
def parse_prd(page_id: str = Query(...)):
    html = confluence_fetcher.fetch_prd_content(page_id)
    md = doc_parser.html_to_markdown(html)
    chunks = doc_parser.chunk_markdown(md)
    features = feature_extractor.extract_features(chunks)
    plans = testplan_generator.generate_test_plan(features)
    cases = [testcase_generator.generate_test_cases(p) for p in plans]
    return {"features": features, "plans": plans, "cases": cases}

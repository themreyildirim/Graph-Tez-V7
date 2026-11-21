"""İnsan kararını teknik/ajan incelemesinden ayrı tutan saf olay doğrulayıcı.

Yazma/yayınlama veya mevcut QA durumunu değiştirme işlevi yoktur. Kaydı yapan
kullanıcının kimliği bu teknik kontrolden bağımsız olarak yetkilendirilmelidir.
"""
from datetime import datetime
from pathlib import Path
import wp12_source_case as c
from wp12_api_security import public_sha

RUN=c.ROOT/'reports/qa/WP12/openai_corrected_account_user_runs_v1/20261108_164416_6fd67845f94e4074818e71b22470cf22'


def validate_event(event,authorized_reviewer_ids):
    required={'version','case_id','run_id','raw_response_sha256','reviewed_item_indices','quote_ids',
        'decision','reviewer_id','reviewer_role','reviewed_at','user_confirmation_reference'}
    if not isinstance(event,dict) or set(event)!=required:raise ValueError('HUMAN_EVENT_FIELDS')
    if event['version']!='WP12-human-decision-event-v1' or event['case_id']!='S01' or event['run_id']!=RUN.name:
        raise ValueError('HUMAN_EVENT_SCOPE')
    if not event['reviewer_id'] or event['reviewer_id'] not in authorized_reviewer_ids:
        raise ValueError('NAMED_AUTHORIZED_REVIEWER_REQUIRED')
    if not event['reviewer_role'] or not event['user_confirmation_reference']:raise ValueError('REVIEW_ATTRIBUTION_REQUIRED')
    when=datetime.fromisoformat(event['reviewed_at'])
    if when.tzinfo is None:raise ValueError('TIMEZONE_REQUIRED')
    if event['decision'] not in ['APPROVED','REJECTED','NEEDS_CHANGES']:raise ValueError('EXPLICIT_DECISION_REQUIRED')
    if event['raw_response_sha256']!=public_sha(RUN/'inference_response_raw.json'):raise ValueError('REVIEWED_RESPONSE_CHANGED')
    actual=c.read(RUN/'validated_JSON.json')['result']['items']
    expected=[x['evidence_ids'][0] for x in actual]
    if event['reviewed_item_indices']!=[1,2] or event['quote_ids']!=expected:raise ValueError('EXACT_TWO_ITEM_SOURCE_SCOPE_REQUIRED')
    return {'event_format_and_registered_attribution_valid':True,'source_artifacts_modified':False,
        'identity_cryptographically_verified':False,'automatic_publication':False,
        'decision_not_written_by_validator':True}

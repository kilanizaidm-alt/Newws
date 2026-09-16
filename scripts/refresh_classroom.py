"""Publish independent dated source links even when AI is unavailable."""
import concurrent.futures
from datetime import datetime, timezone, timedelta
import json
import urllib.error
import traceback
import update_news as u


def refresh_reports(now):
    reports, failed = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [(feed, pool.submit(u.read_feed, feed, now)) for feed in u.FEEDS]
        for feed, job in jobs:
            try:
                reports.extend(job.result())
            except Exception:
                failed.append(f"{feed[0]} ({feed[1]})")
    # Publish headlines/links only. Never republish full source articles.
    unique = {r['url']: r for r in reports}
    items = [{k: r[k] for k in ('title','url','publisher','language','published_at')}
             for r in unique.values()]
    items.sort(key=lambda r: r['published_at'], reverse=True)
    target = u.DATA / 'reports.json'
    if items:
        u.atomic_json(target, {'fetched_at': now.isoformat(),
            'window_start': (now-timedelta(hours=72)).isoformat(),
            'reports': items, 'failed_feeds': failed})
    # Do not re-date or replace old reports when all feeds fail.
    return len(items), failed


def enable_detailed_glossary():
    extra = ('part_of_speech','meaning_ar','collocations','translation_note_ar')
    for field in extra:
        u.FORMAT['glossary'][0][field] = ''
    u.SYSTEM += '''\nFor EVERY glossary entry also supply part_of_speech (English),
meaning_ar (a concise contextual explanation in Arabic), collocations
(two useful English expressions with their Arabic equivalents, as a string),
and translation_note_ar (a specific ambiguity or common mistranslation).
Do not claim external terminology verification when no supplied source supports it.
The example_en must remain an exact sentence from a learning summary.
Review Arabic meaning separately from idiomatic Arabic style.\n'''
    original = u.validate
    def detailed_validate(lesson, sources):
        original(lesson, sources)
        for term in lesson['glossary']:
            if not all(u.nonempty(term.get(field), 1500) for field in extra):
                raise ValueError('Missing detailed glossary fields')
    u.validate = detailed_validate


def main():
    now = datetime.now(timezone.utc)
    count, failed = refresh_reports(now)
    enable_detailed_glossary()
    status = 'unavailable'
    code = None
    try:
        u.main()
        latest = u.DATA / 'latest.json'
        if latest.exists():
            lesson = json.loads(latest.read_text(encoding='utf-8'))
            if not lesson.get('demo'):
                status = ('ready' if str(lesson.get('generated_at','')).startswith(now.date().isoformat())
                          else 'retained')
    except Exception as error:
        # No response bodies, credentials, or external messages in logs/data.
        if isinstance(error, urllib.error.HTTPError):
            code = error.code
        frames=traceback.extract_tb(error.__traceback__)
        last=frames[-1] if frames else None
        location=f'{last.name}:{last.lineno}' if last else 'unknown'
        print(f'Optional lesson refresh failed: {type(error).__name__}; HTTP={code}; at={location}',flush=True)
    u.atomic_json(u.DATA / 'refresh-status.json', {
        'attempted_at': now.isoformat(), 'lesson_status': status,
        'report_count': count, 'failed_feeds': failed})
    print(f'Publisher links refreshed: {count}. Lesson status: {status}.')
    # A missing AI lesson is not a publishing failure. Total feed failure is.
    if not count:
        raise RuntimeError('No fresh publisher feed available; existing reports retained')

if __name__ == '__main__':
    main()

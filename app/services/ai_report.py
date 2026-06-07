"""
GPT-4o powered Korean-language report generation.
Uses AsyncOpenAI client; API key and model read from settings.
"""
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.report import AnomalyResult

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def generate_saas_optimize_report(
    subscription_id: int,
    subscription_name: str,
    provider: str,
    monthly_fee: float,
    total_seats: int,
    used_seats: int,
    wasted_amount: float,
    risk_level: str,
    ghost_account_count: int,
) -> str:
    unused_seats = total_seats - used_seats
    utilization_pct = round(used_seats / total_seats * 100, 1) if total_seats else 0

    prompt = f"""당신은 CFO를 보좌하는 SaaS 비용 최적화 전문가입니다.
아래 SaaS 구독 현황 데이터를 분석하고 경영진이 즉시 이해할 수 있는 한국어 리포트를 작성하세요.

[구독 정보]
- 서비스명: {subscription_name} ({provider})
- 월 구독료: {int(monthly_fee):,}원
- 전체 시트: {total_seats}석 / 사용 시트: {used_seats}석 / 미사용 시트: {unused_seats}석
- 시트 활용률: {utilization_pct}%
- 월 낭비 금액: {int(wasted_amount):,}원
- 위험 등급: {risk_level}
- 고스트 계정 수 (45일 이상 미사용): {ghost_account_count}명

다음 구조로 리포트를 작성하세요:
1. 현황 요약 (2~3문장)
2. 문제점 분석 (낭비 원인, 위험 수준 판단 근거)
3. 즉시 실행 가능한 최적화 권고안 (구체적인 수치 포함, 절감 예상액 제시)
4. 장기 개선 방향 (1~2가지)

리포트는 명확하고 간결하게, 400자 이내로 작성하세요."""

    response = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


async def generate_anomaly_explain_report(anomaly: AnomalyResult) -> str:
    direction = "초과" if anomaly.z_score > 0 else "미달"
    prompt = f"""당신은 CFO를 보좌하는 재무 이상 탐지 전문가입니다.
아래 부서의 이번 달 지출 이상 탐지 결과를 분석하고 경영진에게 보고할 한국어 리포트를 작성하세요.

[이상 탐지 결과]
- 부서명: {anomaly.department_name}
- 이번 달 지출: {int(anomaly.current_spending):,}원
- 3개월 평균 지출: {int(anomaly.mean_spending):,}원
- Z-score: {anomaly.z_score} (기준치 초과 여부: {'이상 감지됨' if anomaly.is_anomaly else '정상 범위'})
- 평균 대비 {direction} 금액: {int(anomaly.excess_amount):,}원

다음 구조로 리포트를 작성하세요:
1. 이상 탐지 결과 요약 (1~2문장)
2. 가능한 원인 분석 (3가지 이내, 재무적 관점)
3. 권고 조치 (담당자 확인 요청, 증빙 검토 등 구체적 액션)

리포트는 명확하고 간결하게, 350자 이내로 작성하세요."""

    response = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

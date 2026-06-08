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
아래 SaaS 구독 현황 데이터를 분석하고 경영진이 즉시 의사결정할 수 있는 한국어 리포트를 작성하세요.

[구독 정보]
- 서비스명: {subscription_name} ({provider})
- 월 구독료: {int(monthly_fee):,}원
- 전체 시트: {total_seats}석 / 사용 시트: {used_seats}석 / 미사용 시트: {unused_seats}석
- 시트 활용률: {utilization_pct}%
- 월 낭비 금액: {int(wasted_amount):,}원 (연간 환산: {int(wasted_amount * 12):,}원)
- 위험 등급: {risk_level}
- 고스트 계정 수 (45일 이상 미사용): {ghost_account_count}명

아래 형식을 반드시 지켜 작성하세요.

■ 현황 요약
(2~3문장. 핵심 수치를 포함하여 현재 상황을 객관적으로 서술)

■ 문제점 분석
(낭비 발생 원인, 위험 등급 판단 근거를 재무적 관점에서 서술)

■ 즉시 실행 권고안
(구체적인 수치와 함께 실행 가능한 조치 2~3가지 제시. 각 조치별 예상 절감액 명시)

■ 장기 개선 방향
(1~2가지. 운영 프로세스 관점에서 제안)

■ 핵심 한 줄 요약
(의사결정자를 위한 한 문장 결론)

전문적이고 간결하게 작성하되, 근거 없는 수치나 과장된 표현은 사용하지 마세요."""

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
- 평균 대비 {direction} 금액: {int(anomaly.excess_amount):,}원
- Z-score: {anomaly.z_score:.2f} (2.0 초과 시 이상 판정)
- 탐지 결과: {'⚠️ 이상 감지됨' if anomaly.is_anomaly else '✅ 정상 범위'}

아래 형식을 반드시 지켜 작성하세요.

■ 이상 탐지 요약
(1~2문장. Z-score와 초과 금액을 포함하여 상황을 명확히 서술)

■ 가능한 원인 분석
(재무적 관점에서 3가지 이내로 제시. 각 원인은 번호로 구분)

■ 권고 조치
(담당자 확인, 증빙 검토 등 즉시 실행 가능한 구체적 액션 2~3가지)

■ 핵심 한 줄 요약
(의사결정자를 위한 한 문장 결론)

전문적이고 간결하게 작성하되, 확인되지 않은 사실을 단정하지 마세요."""

    response = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

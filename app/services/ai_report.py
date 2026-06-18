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
해당 문장을 그대로 따라 작성하지 않고, 각 항목에 맞는 내용을 작성합니다.

■ 현황 요약
(2~3문장. 핵심 수치를 포함하여 현재 상황을 객관적으로 서술)

■ 위험도 기준
기본적으로 활용률을 90%이상은 Low, 70~89%는 Medium, 50~69%는 High 50%미만은 Critical로 판단합니다.
고스트 계정률이 10%이하라면 기존 평가가 바뀌지 않으며,10%~20%라면 한 단계 높은 위험등급으로 판단합니다. 
20~30%라면 두 단계 높은 위험등급으로, 30%이상이라면 세 단계 높은 위험등급으로 판단합니다.
또한 전년도 동월 대비, 전월 대비 시트활용률이 모두 올랐다면 한 단계 낮은 위험 등급으로 판단하고,
반대로 시트 활용률이 모두 떨어졌다면 한 단계 높은 위험 등급으로 판단합니다.
그 외에 시트 활용률 변화가 위험도에 미치는 영향은 없습니다.(회사를 normal한 회사로 가정하여 작성했기 때문에)

■ 문제점 분석
(낭비 발생 원인, 위험 등급 판단 근거를 재무적 관점에서 서술)

■ 즉시 실행 권고안
(구체적인 수치와 함께 실행 가능한 조치 2~3가지 제시. 각 조치별 예상 절감액 명시)
1.Critical 위험 등급인 경우 해당 부서에 경고 처리를 하며 즉시 시트 수를 50%로 줄이는 조치를 권고하며, 
예상 절감액은 월 낭비 금액의 50%로 추산됩니다.
2. High 위험 등급인 경우 해당 부서에 경고 처리를 하며 즉시 시트 수 20%를 줄이는 조치를 권고하며, 
예상 절감액은 월 낭비 금액의 20%로 추산됩니다. 다만 오로지 시트 활용률을 통해서만 High 위험 등급이 매겨진 경우
시트 수 10%를 추가로 줄이는 조치를 권고하며, 이 경우 예상 절감액은 30%로 추산됩니다.
3. Medium 위험 등급인 경우 해당 부서에 현 상황을 안내합니다. 
다만 오로지 시트 활용률을 통해서만 Medium 위험 등급이 매겨진 경우 시트 수를 10% 줄이는 조치를 권고하며, 
이 경우 예상 절감액은 월 낭비 금액의 10%로 추산됩니다.
4. Low 위험 등급인 경우 즉시 실행 권고안은 없습니다.

■ 장기 개선 방향
(1~2가지. 운영 프로세스 관점에서 제안)
1. 기업별 맞춤형 위험도 기준 운영 프로세스
 기존의 획일적인 연도별, 월별로 구분하는게 아니라 각 회사의 프로세스 및 진행중인 프로젝트 특성을 반영하여 위험도 기준을 변화하는 시스템을 구축하는 것으로 개선합니다.
또한 각 회사별 위험 판단 결과에 대한 피드백을 지속적으로 수집하여 위험도 기준과 평가 프로세스를 지속적으로 개선하는 시스템을 구축하는 것을 권고합니다.
2. 부서별 예산 예측 및 사전 경고 체제
 회사에서 계획한 지출을 유도하고 초과 예산 지출을 방지할 수 있는 방법을 구축합니다. 즉, 현재 사용하는 추세를 기반으로 얼마나 지출이 될 것인지 예측하는 시스템을 구축합니다.


■ 핵심 한 줄 요약
(의사결정자를 위한 한 문장 결론)
Aegis-Fi를 도입한다면 SaaS낭비 비용을 줄이고, AI 기반의 통제 시스템을 갖추어 기업 지출 관리 체계를 고도화 할 수 있다는 내용을 만들어줘.
앞서 작성된 문장을 바탕으로 만들면 좋습니다.

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
Z-score 2.0 초과시 이상으로 판단하며, 이번 달 지출이 3개월 평균 대비 얼마만큼 초과되었는지를 명확히 서술합니다.
Z-score 3.0 초과시에는 심각한 이상으로 판단하여 그 점도 명확히 서술합니다.

■ 가능한 원인 분석(해당 원인을 모두 사용하지 않고, 어떤 상황이 어울리는지 추측해서 작성하기)
(재무적 관점에서 3가지 이내로 제시. 각 원인은 번호로 구분)
1. 프로젝트성 일시 지출 증가 or 일시적인 SaaS 라이선스 또는 구독 증가
->  Z-score가 높더라도 이런 경우에는 일시적인 지출 증가로 판단할 수 있습니다.
2. 예산 정책 미준수 또는 비정상 결제 : 예산 승인 절차를 거치지 않은 지출이 발생했거나, 기존 예산 범위를 초과하여 결제된 경우입니다.
3. 이외의 기타 원인 : 위의 두 가지 원인으로 설명되지 않는 경우, 추가 조사가 필요한 상황입니다. 

■ 권고 조치 (0번부터 3번까지 모두 쓰지 말고, 상황에 맞게 작성하기.)
(담당자 확인, 증빙 검토 등 즉시 실행 가능한 구체적 액션 2~3가지)
0. 만약 이상거래가 아닌 것으로 판단 될 경우, 해당 부서나 해당 직원에 아무런 권고 조치를 하지 않습니다.
1. 이상이 감지된 부서의 담당자에게 이번 달 지출 내역과 관련 증빙 자료를 제출하도록 요청합니다.
2. 재무 이상 탐지 담당자에게 이번 달 지출 내역과 관련 증빙 자료를 검토하도록 요청합니다.
3. 실제로 이상 거래일 경우 해당 결제를 한 직원에게 패널티를 부과합니다. 패널티는 회사 정책에 따라 결정됩니다.

■ 핵심 한 줄 요약
(의사결정자를 위한 한 문장 결론)
Aegis-Fi를 도입한다면 지출의 이상탐지를 보다 쉽고 정확하게 판단하여 재무 리스크를 줄이고, 
AI 기반의 통제 시스템을 갖추어 기업 지출 관리 체계를 고도화 할 수 있다는 내용으로
앞서 작성된 문장을 바탕으로 만들어주세요.

전문적이고 간결하게 작성하되, 확인되지 않은 사실을 단정하지 마세요."""

    response = await _get_client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

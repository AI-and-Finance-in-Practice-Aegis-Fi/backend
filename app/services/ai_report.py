"""
Korean report generation for Aegis-Fi.

This module keeps the FastAPI/backend-facing async function signatures intact,
while applying the safer prompt and calculation rules from excel_report_runner_final_v10.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.report import AnomalyResult

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _calculate_saas_risk_level(utilization_pct: float, ghost_rate: float = 0.0) -> str:
    """Calculate SaaS risk level consistently with the Excel runner rules."""
    if utilization_pct >= 90:
        base_level = "Low"
    elif utilization_pct >= 70:
        base_level = "Medium"
    elif utilization_pct >= 50:
        base_level = "High"
    else:
        base_level = "Critical"

    levels = ["Low", "Medium", "High", "Critical"]
    index = levels.index(base_level)

    if ghost_rate >= 30:
        index += 3
    elif ghost_rate >= 20:
        index += 2
    elif ghost_rate >= 10:
        index += 1

    return levels[min(index, len(levels) - 1)]


def _build_saas_prompt(
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
    unused_seats = max(total_seats - used_seats, 0)
    utilization_pct = round(used_seats / total_seats * 100, 1) if total_seats else 0.0
    ghost_rate = round(ghost_account_count / total_seats * 100, 1) if total_seats else 0.0

    # 서버 DB의 risk_level 값이 오래되었거나 seed 데이터와 어긋나도,
    # 리포트 기준은 v10과 동일하게 코드에서 다시 계산합니다.
    calculated_risk_level = _calculate_saas_risk_level(utilization_pct, ghost_rate)
    final_risk_level = calculated_risk_level or risk_level

    if final_risk_level == "Critical":
        action_rule = "부서에 경고 처리 후 미사용 시트 범위 내에서 전체 시트의 50%까지 감축을 권고합니다."
        reduction_rate = 0.50
    elif final_risk_level == "High":
        action_rule = "부서 책임자에게 개선 권고 후 미사용 시트 범위 내에서 전체 시트의 30% 감축을 권고합니다."
        reduction_rate = 0.30
    elif final_risk_level == "Medium":
        action_rule = "부서에 현 상황을 안내하고 미사용 시트 범위 내에서 전체 시트의 10% 감축을 권고합니다."
        reduction_rate = 0.10
    else:
        action_rule = "즉시 감축 권고는 하지 않습니다. 정기 모니터링만 권고합니다."
        reduction_rate = 0.0

    # 절감액은 월 낭비액의 비율이 아니라 실제 감축 시트 수 × 좌석당 월 단가로 계산합니다.
    target_cut = int(round(total_seats * reduction_rate))
    recommended_cut = min(unused_seats, target_cut) if reduction_rate > 0 else 0
    per_seat_fee = int(round(monthly_fee / total_seats)) if total_seats else 0
    expected_saving = recommended_cut * per_seat_fee

    if utilization_pct >= 90:
        utilization_band = "90% 이상 구간이므로 Low 기준에 해당합니다."
        management_comment = "사내 관리 기준을 충족하고 있습니다."
    elif utilization_pct >= 70:
        utilization_band = "70~89% 구간이므로 Medium 기준에 해당합니다."
        management_comment = "사내 관리 기준에 근접하지만 추가 최적화 여지가 있습니다."
    elif utilization_pct >= 50:
        utilization_band = "50~69% 구간이므로 High 기준에 해당합니다."
        management_comment = "사내 관리 기준(70%)을 하회하고 있습니다."
    else:
        utilization_band = "50% 미만 구간이므로 Critical 기준에 해당합니다."
        management_comment = "사내 관리 기준(70%)을 크게 하회하고 있습니다."

    if ghost_rate >= 30:
        ghost_risk_comment = "고스트 계정률이 30% 이상이므로 위험도 상향 요인입니다."
    elif ghost_rate >= 20:
        ghost_risk_comment = "고스트 계정률이 20% 이상이므로 위험도 상향 요인입니다."
    elif ghost_rate >= 10:
        ghost_risk_comment = "고스트 계정률이 10% 이상이므로 위험도 상향 요인입니다."
    else:
        ghost_risk_comment = f"고스트 계정률은 {ghost_rate}%로 위험도 상향 기준에는 미달합니다."

    return f"""당신은 CFO를 보좌하는 SaaS 비용 최적화 전문가입니다.
아래 SaaS 구독 현황 데이터를 분석하고 경영진이 즉시 의사결정할 수 있는 한국어 리포트를 작성하세요.

[구독 정보]
- 구독 ID: {subscription_id}
- 서비스명: {subscription_name} ({provider})
- 월 구독료: {int(monthly_fee):,}원
- 좌석당 월 단가: {per_seat_fee:,}원
- 전체 시트: {total_seats}석 / 사용 시트: {used_seats}석 / 미사용 시트: {unused_seats}석
- 시트 활용률: {utilization_pct}%
- 활용률 관리 코멘트: {management_comment}
- 월 낭비 금액: {int(wasted_amount):,}원 (연간 환산: {int(wasted_amount * 12):,}원)
- 기존 입력 위험 등급: {risk_level}
- 최종 위험 등급: {final_risk_level}
- 고스트 계정 수: {ghost_account_count}명
- 고스트 계정률: {ghost_rate}%
- 고스트 계정 위험도 설명: {ghost_risk_comment}
- 위험도 산정 기준: 활용률 90% 이상 Low, 70~89% Medium, 50~69% High, 50% 미만 Critical. 고스트 계정률 10% 이상부터 위험도 상향.
- 활용률 기준 설명: {utilization_band}
- 이번 건 권고 규칙: {action_rule}
- 권고 감축 시트 수: {recommended_cut}석
- 절감액 계산식: {recommended_cut}석 × 좌석당 월 단가 {per_seat_fee:,}원 = 월 {expected_saving:,}원
- 권고 기준 예상 절감액: 월 {expected_saving:,}원 / 연 {expected_saving * 12:,}원

아래 형식을 반드시 지켜 작성하세요.
해당 문장을 그대로 따라 작성하지 않고, 각 항목에 맞는 내용을 작성합니다.

■ 현황 요약
(2~3문장.
전체 시트, 사용 시트, 미사용 시트, 활용률, 월/연간 낭비 금액을 포함하세요.
활용률이 70% 미만이면 반드시 "사내 관리 기준(70%)을 하회하고 있다"는 의미를 자연스럽게 포함하세요.)

■ 위험도 기준
(위험 등급 {final_risk_level}은 반드시 활용률 기준 설명과 고스트 계정률 설명을 함께 사용해 작성하세요.
반드시 다음 내용을 포함하세요.
1. 현재 활용률이 어느 구간에 해당하는지
2. 고스트 계정률이 위험도 상향 기준에 해당하는지 여부
3. 최종 위험 등급이 무엇인지
"{utilization_band}"라는 의미를 자연스럽게 설명하세요.
활용률 {utilization_pct}%를 50% 미만이라고 쓰거나, "50% 미만보다 낮다" 같은 잘못된 비교 표현을 쓰지 마세요.
위험 등급을 바꾸지 마세요.)

■ 문제점 분석
(주요 낭비 원인은 미사용 시트입니다.
고스트 계정 수가 적고 영향이 제한적이라면 고스트 계정보다 미사용 시트 문제를 중심으로 서술하세요.
고스트 계정이 전체 비용 낭비의 주된 원인인 것처럼 작성하지 마세요.
없는 추세 데이터, 전월 대비, 전년 대비 내용은 언급하지 마세요.)

■ 즉시 실행 권고안
(구체적인 수치와 함께 실행 가능한 조치 2~3가지를 제시하세요.
권고안은 경고나 검토보다 실제 비용 절감 효과가 큰 조치를 우선 제시하세요.)
1. 반드시 "{recommended_cut}석 감축"과 "{recommended_cut}석 × {per_seat_fee:,}원 = 월 {expected_saving:,}원 / 연 {expected_saving * 12:,}원 절감"을 포함하세요.
2. 절감액을 월 낭비 금액의 비율로 계산하지 마세요. 절감액은 반드시 감축 시트 수 × 좌석당 월 단가로 계산하세요.
3. 고스트 계정이 1명 이상이면 계정 회수 또는 재배정 조치를 포함하되, 고스트 계정이 비용 낭비의 주된 원인인 것처럼 과장하지 마세요.
4. Critical 위험 등급일 때만 "경고"라는 표현을 사용하세요. High 또는 Medium에서는 "개선 권고", "현황 안내", "회수", "감축", "재배정" 중심으로 작성하세요.
5. "고려", "검토", "확인 필요", "점검 필요"처럼 모호한 표현은 사용하지 말고 실행 지시형으로 작성하세요.

■ 핵심 한 줄 요약
반드시 다음 형식으로 한 문장만 작성하세요.
"현재 상태를 유지할 경우 연간 {int(wasted_amount * 12):,}원의 비용 낭비가 예상되며, 미사용 시트 {unused_seats}석 중 {recommended_cut}석 회수만으로도 연간 {expected_saving * 12:,}원의 비용 절감이 가능합니다."

중요:
입력 데이터에 없는 사실을 추론하지 마세요.
전월 대비, 전년 대비, 증가 추세, 감소 추세, 향후 상승 가능성, 향후 하락 가능성은 관련 데이터가 제공된 경우에만 사용하세요.
위험 등급은 코드에서 계산된 값이므로 리포트에서 변경하지 마세요.
전문적이고 간결하게 작성하되, 근거 없는 수치나 과장된 표현은 사용하지 마세요.
"""


def _build_anomaly_prompt(anomaly: AnomalyResult) -> str:
    direction = "초과" if anomaly.z_score > 0 else "미달"
    abs_z = abs(anomaly.z_score)
    excess_amount_abs = abs(anomaly.excess_amount)

    if abs_z < 2.0:
        severity = "정상"
        severity_comment = "절댓값 2.0 미만으로 정상 범위입니다."
        action_summary = "별도 제재나 긴급 조치 없이 정기 모니터링을 유지합니다."
    elif abs_z < 3.0:
        severity = "주의"
        severity_comment = "절댓값 2.0 이상 3.0 미만으로 주의 구간입니다."
        action_summary = "거래 내역과 승인 근거를 확인합니다."
    elif abs_z < 4.0:
        severity = "경고"
        severity_comment = "절댓값 3.0 이상 4.0 미만으로 경고 구간입니다."
        action_summary = "부서 담당자 확인과 증빙 대조를 즉시 진행합니다."
    else:
        severity = "심각"
        severity_comment = "절댓값 4.0 이상으로 심각 구간입니다."
        action_summary = "거래 검증, 승인 내역 대조, 담당자 확인을 즉시 진행합니다."

    return f"""당신은 CFO를 보좌하는 재무 이상 탐지 전문가입니다.
아래 부서의 이번 달 지출 이상 탐지 결과를 분석하고 경영진에게 보고할 한국어 리포트를 작성하세요.

[이상 탐지 결과]
- 부서명: {anomaly.department_name}
- 이번 달 지출: {int(anomaly.current_spending):,}원
- 최근 기준 평균 지출: {int(anomaly.mean_spending):,}원
- 평균 대비 {direction} 금액: {int(excess_amount_abs):,}원
- Z-score: {anomaly.z_score:.2f}
- 이상 강도: {severity}
- 이상 강도 설명: {severity_comment}
- 탐지 결과: {'⚠️ 이상 감지됨' if anomaly.is_anomaly else '✅ 정상 범위'}
- 권고 방향: {action_summary}

[이상 강도 기준]
- 정상: |Z-score| < 2.0
- 주의: 2.0 ≤ |Z-score| < 3.0
- 경고: 3.0 ≤ |Z-score| < 4.0
- 심각: |Z-score| ≥ 4.0

아래 형식을 반드시 지켜 작성하세요.

■ 이상 탐지 요약
(2문장 이내로 작성하세요.
반드시 아래 5개 수치를 모두 포함하세요.
1. 이번 달 지출
2. 최근 기준 평균 지출
3. 평균 대비 초과/미달 금액
4. Z-score
5. 이상 강도

예시 형식:
"이번 달 개발팀 지출은 40,439,648원으로, 최근 기준 평균 지출 34,643,334원 대비 5,796,314원 초과되었습니다.
Z-score는 6.98로 심각 구간에 해당합니다."

정상 범위라면 과장하지 말고 정상이라고 쓰세요.
주의/경고/심각 구간이라면 즉시 확인이 필요한 이유를 재무 관점에서 간결하게 설명하세요.)

■ 가능한 원인 분석
(입력 데이터만 기반으로 작성하세요.
프로젝트성 일시 지출, 예산 초과 집행, SaaS 라이선스 증가, 대규모 구매, 비정상 결제 중 실제 데이터와 가장 일치하는 원인만 선택하세요.
최대 2개까지만 작성하세요.

평균 대비 초과인 경우에는 지출 증가 원인을 중심으로 작성하세요.
평균 대비 미달인 경우에는 예산 미집행, 프로젝트 지연, 예정 구매 취소처럼 지출 감소 원인을 중심으로 작성하세요.
미달 상황에서 "예산 초과 집행"이라고 쓰지 마세요.

입력 데이터에 없는 거래처명, 직원명, 구체적 구매 품목은 만들지 마세요.
확정되지 않은 이상 거래를 부정행위처럼 단정하지 마세요.)

■ 권고 조치
(즉시 실행 가능한 조치 2~3가지를 제시하세요.
반드시 다음 순서를 우선하세요.
1. 거래 내역 검증
2. 예산 승인 내역 확인
3. 담당자 확인
4. 실제 이상 거래로 확정된 경우에만 후속 조치
이상 거래가 확정되지 않은 상태에서 징계, 패널티, 책임 추궁을 먼저 권고하지 마세요.
정상 범위인 경우에는 별도 조치 없이 정기 모니터링 유지라고 작성하세요.)

■ 핵심 한 줄 요약
반드시 한 문장으로 작성하세요.
정상 범위가 아닌 경우:
"이번 달 지출은 {int(anomaly.current_spending):,}원으로 최근 기준 평균 {int(anomaly.mean_spending):,}원 대비 {int(excess_amount_abs):,}원 {direction}되었으며, Aegis-Fi 기반 자동 이상탐지를 통해 거래 검증과 승인 내역 대조가 필요합니다."
정상 범위인 경우:
"이번 달 지출은 정상 범위에 있으며, Aegis-Fi 기반 자동 모니터링을 통해 재무 리스크를 지속적으로 관리할 수 있습니다."

중요:
입력 데이터에 없는 사실을 추론하지 마세요.
전월 대비, 전년 대비, 증가 추세, 감소 추세, 향후 상승 가능성, 향후 하락 가능성은 관련 데이터가 제공된 경우에만 사용하세요.
확정되지 않은 이상 거래를 비정상 결제, 부정 사용, 정책 위반으로 단정하지 마세요.
리포트는 CFO가 바로 의사결정에 사용할 수 있도록 단정적이되, 근거 없는 단정은 피하세요.
전문적이고 간결하게 작성하세요.
"""


async def _call_openai_report(prompt: str, max_tokens: int = 1200) -> str:
    """Call OpenAI while supporting both chat-completions models and GPT-5 responses models."""
    model = settings.OPENAI_MODEL
    client = _get_client()

    if model.startswith("gpt-5"):
        response = await client.responses.create(
            model=model,
            input=prompt,
            reasoning={"effort": "low"},
            max_output_tokens=max(max_tokens, 8000),
        )
        text = getattr(response, "output_text", "") or ""
        return text.strip()

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


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
    prompt = _build_saas_prompt(
        subscription_id=subscription_id,
        subscription_name=subscription_name,
        provider=provider,
        monthly_fee=monthly_fee,
        total_seats=total_seats,
        used_seats=used_seats,
        wasted_amount=wasted_amount,
        risk_level=risk_level,
        ghost_account_count=ghost_account_count,
    )
    return await _call_openai_report(prompt, max_tokens=1600)


async def generate_anomaly_explain_report(anomaly: AnomalyResult) -> str:
    prompt = _build_anomaly_prompt(anomaly)
    return await _call_openai_report(prompt, max_tokens=1400)

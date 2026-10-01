import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from app.services.chat_guidance import service_guidance, GUIDES, policy_fallback
from test_workspace import isolated_function
from app import schemas


class GuidanceTests(unittest.TestCase):
    def test_order_variants(self):
        for question in ['지금 내가 상품을 주문하려면 어떻게 해야하지', '상품 어떻게 구매해?', '주문하는 법 알려줘', '구매 절차 알려줘', '이 상품 주문해줘']:
            with self.subTest(question=question):
                self.assertEqual(service_guidance(question), GUIDES['order'])

    def test_policies_and_history_are_not_purchase_instructions(self):
        for question in ['주문 취소 어떻게 해?', '환불 방법 알려줘', '배송 언제 와?', '내 주문 내역 조회해줘', '내 회원정보 알려줘']:
            self.assertIsNone(service_guidance(question))

    def test_service_features(self):
        for question, topic in [('상품 등록 어떻게 해?', 'product'), ('회원가입 어떻게 해?', 'account'), ('문서 수정 어떻게 해?', 'document')]:
            self.assertEqual(service_guidance(question), GUIDES[topic])

    def route(self, action='get_policy'):
        classify = MagicMock(return_value=action)
        search = MagicMock(return_value=['정책'])
        generate = MagicMock(return_value='응답불가합니다')
        cache = MagicMock()
        model = MagicMock(side_effect=lambda **kw:SimpleNamespace(**kw))
        fn = isolated_function('app/routers/chat.py', 'create_chat', schemas=schemas,
            models=SimpleNamespace(Member=object, Chat=model), observe=lambda **kw:lambda f:f,
            service_guidance=service_guidance, GUIDES=GUIDES, policy_fallback=policy_fallback,
            classify_message=classify, search_policy=search, semantic_cache=cache,
            load_chat_history=MagicMock(return_value=[]), generate_response_langchain_memory=generate,
            my_page=MagicMock(), my_orders=MagicMock(), _format_profile=MagicMock(), _format_orders=MagicMock())
        return fn, classify, search, cache

    def test_actual_route_bypasses_llm_search_and_cached_failure_for_order_help(self):
        fn, classify, search, cache = self.route()
        db=MagicMock()
        result=fn(schemas.ChatRequest(message='지금 내가 상품을 주문하려면 어떻게 해야하지'), db, SimpleNamespace(id=1))
        self.assertEqual(result.response, GUIDES['order'])
        classify.assert_not_called()
        search.assert_not_called()
        cache.search.assert_not_called()
        db.commit.assert_called_once()

    def test_policy_refusal_becomes_actionable_fallback(self):
        fn, _, _, cache = self.route()
        result=fn(schemas.ChatRequest(message='환불 규정'), MagicMock(), SimpleNamespace(id=1))
        self.assertEqual(result.response, policy_fallback())
        cache.store.assert_not_called()

    def test_unknown_intent_does_not_search_unrelated_policies(self):
        fn, _, search, _ = self.route('unknown')
        result=fn(schemas.ChatRequest(message='무엇을 할 수 있나요?'), MagicMock(), SimpleNamespace(id=1))
        self.assertEqual(result.response, GUIDES['help'])
        search.assert_not_called()

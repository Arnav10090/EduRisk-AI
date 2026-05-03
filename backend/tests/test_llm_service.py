"""
Test LLM service with mocked Groq API responses.

Tests verify that the LLMService:
1. Returns expected summaries on successful API calls
2. Returns fallback messages on timeouts
3. Returns fallback messages when API key is missing
4. Handles rate limit errors gracefully
5. Degrades gracefully without failing predictions

Feature: edurisk-submission-improvements
Requirements: Task 23 (Requirement 29), Task 24 (Requirement 30)
"""

import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.llm_service import LLMService


# Test data fixtures
@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "course_type": "Engineering",
        "institute_tier": 2,
        "cgpa": 7.5,
        "internship_count": 1
    }


@pytest.fixture
def sample_prediction():
    """Sample prediction data for testing."""
    return {
        "risk_score": 45,
        "risk_level": "medium",
        "prob_placed_3m": 0.55,
        "prob_placed_6m": 0.70,
        "prob_placed_12m": 0.85
    }


@pytest.fixture
def sample_risk_drivers():
    """Sample SHAP risk drivers for testing."""
    return [
        {"feature": "internship_score", "value": -0.15, "direction": "negative"},
        {"feature": "cgpa_normalized", "value": 0.08, "direction": "positive"},
        {"feature": "institute_tier", "value": -0.05, "direction": "negative"}
    ]


class TestSuccessfulLLMResponse:
    """
    Test 23.2: Test successful LLM response.
    
    Requirements:
        - 23.2.1: Mock successful Groq API response
        - 23.2.2: Verify LLMService returns expected summary
    """
    
    @pytest.mark.asyncio
    async def test_groq_successful_response(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService returns expected summary on successful Groq API call."""
        # Create mock response object
        mock_choice = MagicMock()
        mock_choice.message.content = "Medium risk student with limited internship experience being the primary concern."
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Patch GROQ_AVAILABLE and AsyncGroq
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary is not None
                assert len(summary) > 0
                assert summary != service.fallback_message
                mock_client.chat.completions.create.assert_called_once()
                
                print("✅ Test passed: Groq API successful response")
    
    @pytest.mark.asyncio
    async def test_anthropic_successful_response(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService returns expected summary on successful Anthropic API call."""
        mock_content = MagicMock()
        mock_content.text = "Medium risk student with limited internship experience."
        
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        
        with patch('backend.services.llm_service.ANTHROPIC_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncAnthropic') as mock_anthropic_class:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_response)
                mock_anthropic_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="anthropic")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary is not None
                assert len(summary) > 0
                assert summary != service.fallback_message
                mock_client.messages.create.assert_called_once()
                
                print("✅ Test passed: Anthropic API successful response")


class TestLLMTimeout:
    """
    Test 23.3: Test LLM timeout.
    
    Requirements:
        - 23.3.1: Mock Groq API timeout
        - 23.3.2: Verify LLMService returns fallback message
        - 23.3.3: Verify no exception raised
    """
    
    @pytest.mark.asyncio
    async def test_groq_timeout_returns_fallback(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService returns fallback message on Groq API timeout."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=asyncio.TimeoutError("Request timed out")
                )
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary == service.fallback_message
                assert "AI summary unavailable" in summary
                
                print("✅ Test passed: Groq API timeout returns fallback")
    
    @pytest.mark.asyncio
    async def test_anthropic_timeout_returns_fallback(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService returns fallback message on Anthropic API timeout."""
        with patch('backend.services.llm_service.ANTHROPIC_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncAnthropic') as mock_anthropic_class:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(
                    side_effect=asyncio.TimeoutError("Request timed out")
                )
                mock_anthropic_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="anthropic")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary == service.fallback_message
                assert "AI summary unavailable" in summary
                
                print("✅ Test passed: Anthropic API timeout returns fallback")


class TestMissingAPIKey:
    """
    Test 23.4: Test missing API key.
    
    Requirements:
        - 23.4.1: Test with LLM_API_KEY not configured
        - 23.4.2: Verify LLMService returns fallback message
        - 23.4.3: Verify warning logged
    """
    
    @pytest.mark.asyncio
    async def test_missing_api_key_returns_fallback(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService handles missing API key gracefully."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("Authentication failed")
                )
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary == service.fallback_message
                
                print("✅ Test passed: Missing API key returns fallback")
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_fallback(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService handles invalid API key gracefully."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("401 Unauthorized")
                )
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="invalid", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary == service.fallback_message
                
                print("✅ Test passed: Invalid API key returns fallback")


class TestRateLimitHandling:
    """
    Test 23.5 & 24: Test rate limit handling with exponential backoff.
    
    Requirements:
        - 23.5.1: Mock Groq API rate limit error
        - 23.5.2: Verify LLMService implements exponential backoff
        - 23.5.3: Verify fallback after max retries
        - 24.1.1: Detect 429 status code from Groq API
        - 24.1.2: Parse Retry-After header if present
        - 24.2.1: Add retry logic with exponential backoff
        - 24.2.2: Start with 1 second delay, double each retry
        - 24.2.3: Max retries: 3
        - 24.2.4: Max delay: 8 seconds
        - 24.3.1: Return fallback message after max retries
        - 24.3.2: Log rate limit events
        - 24.3.3: Don't raise exceptions for rate limits
    """
    
    @pytest.mark.asyncio
    async def test_rate_limit_returns_fallback(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test 24.4.1: Mock 429 response from Groq API.
        Test 24.4.3: Verify fallback after max retries.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("429 Rate Limit Exceeded")
                )
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                # Should return fallback after max retries
                assert summary == service.fallback_message
                
                # Should have attempted max_retries + 1 times (initial + 3 retries)
                assert mock_client.chat.completions.create.call_count == 4
                
                print("✅ Test passed: Rate limit error returns fallback after max retries")
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test 24.4.2: Verify exponential backoff behavior.
        Test 24.2.2: Start with 1 second delay, double each retry.
        Test 24.2.4: Max delay: 8 seconds.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                    mock_client = AsyncMock()
                    mock_client.chat.completions.create = AsyncMock(
                        side_effect=Exception("429 Too Many Requests")
                    )
                    mock_groq_class.return_value = mock_client
                    
                    service = LLMService(api_key="test_key", provider="groq")
                    
                    summary = await service.generate_summary(
                        student_data=sample_student_data,
                        prediction=sample_prediction,
                        top_risk_drivers=sample_risk_drivers
                    )
                    
                    # Verify exponential backoff delays: 1s, 2s, 4s
                    assert mock_sleep.call_count == 3
                    delays = [call[0][0] for call in mock_sleep.call_args_list]
                    
                    assert delays[0] == 1.0  # First retry: 1 second
                    assert delays[1] == 2.0  # Second retry: 2 seconds
                    assert delays[2] == 4.0  # Third retry: 4 seconds
                    
                    print("✅ Test passed: Exponential backoff with correct delays (1s, 2s, 4s)")
    
    @pytest.mark.asyncio
    async def test_max_delay_cap(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test 24.2.4: Max delay: 8 seconds.
        Verify that delay is capped at max_delay even with more retries.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                    mock_client = AsyncMock()
                    mock_client.chat.completions.create = AsyncMock(
                        side_effect=Exception("429 Rate limit exceeded")
                    )
                    mock_groq_class.return_value = mock_client
                    
                    service = LLMService(api_key="test_key", provider="groq")
                    
                    # Verify max_delay is 8 seconds
                    assert service.max_delay == 8.0
                    
                    summary = await service.generate_summary(
                        student_data=sample_student_data,
                        prediction=sample_prediction,
                        top_risk_drivers=sample_risk_drivers
                    )
                    
                    # All delays should be <= 8 seconds
                    delays = [call[0][0] for call in mock_sleep.call_args_list]
                    for delay in delays:
                        assert delay <= 8.0
                    
                    print("✅ Test passed: Delays capped at max_delay (8 seconds)")
    
    @pytest.mark.asyncio
    async def test_retry_after_header_parsing(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test 24.1.2: Parse Retry-After header if present.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                    mock_client = AsyncMock()
                    
                    # Create exception with Retry-After in message
                    mock_client.chat.completions.create = AsyncMock(
                        side_effect=Exception("429 Rate Limit. Retry-After: 3")
                    )
                    mock_groq_class.return_value = mock_client
                    
                    service = LLMService(api_key="test_key", provider="groq")
                    
                    summary = await service.generate_summary(
                        student_data=sample_student_data,
                        prediction=sample_prediction,
                        top_risk_drivers=sample_risk_drivers
                    )
                    
                    # First delay should use Retry-After value (3 seconds)
                    delays = [call[0][0] for call in mock_sleep.call_args_list]
                    assert delays[0] == 3.0
                    
                    print("✅ Test passed: Retry-After header parsed correctly")
    
    @pytest.mark.asyncio
    async def test_rate_limit_logging(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers,
        caplog
    ):
        """
        Test 24.3.2: Log rate limit events.
        Test 24.4.4: Verify rate limit events logged.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    mock_client = AsyncMock()
                    mock_client.chat.completions.create = AsyncMock(
                        side_effect=Exception("429 Rate Limit Exceeded")
                    )
                    mock_groq_class.return_value = mock_client
                    
                    service = LLMService(api_key="test_key", provider="groq")
                    
                    with caplog.at_level(logging.WARNING):
                        summary = await service.generate_summary(
                            student_data=sample_student_data,
                            prediction=sample_prediction,
                            top_risk_drivers=sample_risk_drivers
                        )
                    
                    # Verify rate limit events were logged
                    rate_limit_logs = [
                        record for record in caplog.records
                        if "Rate limit" in record.message
                    ]
                    
                    assert len(rate_limit_logs) >= 3  # At least 3 retry attempts logged
                    
                    # Verify log contains retry information
                    assert any("attempt" in log.message for log in rate_limit_logs)
                    assert any("Retrying" in log.message for log in rate_limit_logs)
                    
                    print("✅ Test passed: Rate limit events logged correctly")
    
    @pytest.mark.asyncio
    async def test_no_exception_raised_on_rate_limit(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test 24.3.3: Don't raise exceptions for rate limits.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    mock_client = AsyncMock()
                    mock_client.chat.completions.create = AsyncMock(
                        side_effect=Exception("429 Rate Limit Exceeded")
                    )
                    mock_groq_class.return_value = mock_client
                    
                    service = LLMService(api_key="test_key", provider="groq")
                    
                    # Should not raise exception
                    try:
                        summary = await service.generate_summary(
                            student_data=sample_student_data,
                            prediction=sample_prediction,
                            top_risk_drivers=sample_risk_drivers
                        )
                        exception_raised = False
                    except Exception:
                        exception_raised = True
                    
                    assert not exception_raised
                    assert summary == service.fallback_message
                    
                    print("✅ Test passed: No exception raised on rate limit")
    
    @pytest.mark.asyncio
    async def test_successful_retry_after_rate_limit(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test that service succeeds if retry succeeds after rate limit.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    mock_client = AsyncMock()
                    
                    # First call fails with rate limit, second succeeds
                    mock_choice = MagicMock()
                    mock_choice.message.content = "Test summary"
                    mock_response = MagicMock()
                    mock_response.choices = [mock_choice]
                    
                    mock_client.chat.completions.create = AsyncMock(
                        side_effect=[
                            Exception("429 Rate Limit"),
                            mock_response
                        ]
                    )
                    mock_groq_class.return_value = mock_client
                    
                    service = LLMService(api_key="test_key", provider="groq")
                    
                    summary = await service.generate_summary(
                        student_data=sample_student_data,
                        prediction=sample_prediction,
                        top_risk_drivers=sample_risk_drivers
                    )
                    
                    # Should return successful summary, not fallback
                    assert summary == "Test summary"
                    assert summary != service.fallback_message
                    
                    # Should have called API twice (initial + 1 retry)
                    assert mock_client.chat.completions.create.call_count == 2
                    
                    print("✅ Test passed: Successful retry after rate limit")
    
    @pytest.mark.asyncio
    async def test_auth_error_no_retry(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """
        Test that authentication errors (401) are not retried.
        Requirement 30.7: Don't retry on authentication errors.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("401 Unauthorized")
                )
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                # Should return fallback immediately without retries
                assert summary == service.fallback_message
                
                # Should have called API only once (no retries for auth errors)
                assert mock_client.chat.completions.create.call_count == 1
                
                print("✅ Test passed: Auth errors not retried")
    
    @pytest.mark.asyncio
    async def test_max_retries_configuration(self):
        """
        Test 24.2.3: Max retries: 3.
        """
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                assert service.max_retries == 3
                assert service.initial_delay == 1.0
                assert service.max_delay == 8.0
                
                print("✅ Test passed: Rate limit configuration correct (max_retries=3, initial_delay=1s, max_delay=8s)")
    
    @pytest.mark.asyncio
    async def test_network_error_returns_fallback(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that LLMService returns fallback message on network error."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("Network error")
                )
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                summary = await service.generate_summary(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                assert summary == service.fallback_message
                
                print("✅ Test passed: Network error returns fallback")


class TestPromptBuilding:
    """Test that prompts are built correctly with student and prediction data."""
    
    def test_prompt_includes_required_data(
        self,
        sample_student_data,
        sample_prediction,
        sample_risk_drivers
    ):
        """Test that _build_prompt includes all required data."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                prompt = service._build_prompt(
                    student_data=sample_student_data,
                    prediction=sample_prediction,
                    top_risk_drivers=sample_risk_drivers
                )
                
                # Verify prompt includes key data
                assert "Engineering" in prompt
                assert "Tier-2" in prompt
                assert "7.5" in prompt
                assert "45/100" in prompt
                assert "medium" in prompt
                assert "internship_score" in prompt
                
                print("✅ Test passed: Prompt includes required data")


class TestFallbackMessage:
    """Test that fallback message is appropriate and helpful."""
    
    def test_fallback_message_format(self):
        """Test that fallback message is user-friendly."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                fallback = service.fallback_message
                
                assert len(fallback) > 0
                assert "unavailable" in fallback.lower()
                assert "SHAP" in fallback or "risk drivers" in fallback
                
                print("✅ Test passed: Fallback message is user-friendly")


class TestProviderSelection:
    """Test that provider selection works correctly."""
    
    def test_groq_provider_initialization(self):
        """Test that Groq provider is initialized correctly."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                assert service.provider == "groq"
                assert service.model == "llama-3.3-70b-versatile"
                mock_groq_class.assert_called_once_with(api_key="test_key")
                
                print("✅ Test passed: Groq provider initialized correctly")
    
    def test_anthropic_provider_initialization(self):
        """Test that Anthropic provider is initialized correctly."""
        with patch('backend.services.llm_service.ANTHROPIC_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncAnthropic') as mock_anthropic_class:
                mock_client = AsyncMock()
                mock_anthropic_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="anthropic")
                
                assert service.provider == "anthropic"
                assert service.model == "claude-sonnet-4-20250514"
                mock_anthropic_class.assert_called_once_with(api_key="test_key")
                
                print("✅ Test passed: Anthropic provider initialized correctly")
    
    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LLMService(api_key="test_key", provider="invalid_provider")
        
        assert "Unsupported provider" in str(exc_info.value)
        
        print("✅ Test passed: Invalid provider raises ValueError")


class TestTimeoutConfiguration:
    """Test that timeout is configured correctly."""
    
    def test_timeout_value(self):
        """Test that timeout is set to 5 seconds."""
        with patch('backend.services.llm_service.GROQ_AVAILABLE', True):
            with patch('backend.services.llm_service.AsyncGroq') as mock_groq_class:
                mock_client = AsyncMock()
                mock_groq_class.return_value = mock_client
                
                service = LLMService(api_key="test_key", provider="groq")
                
                assert service.timeout == 5.0
                
                print("✅ Test passed: Timeout configured to 5 seconds")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

"""
Social Media Content Automation Hub Crew

Uses Perplexity for research tasks and Gemini for content creation.
"""
import logging
from typing import Any
from crewai import Agent, Crew, Process, Task, LLM
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings, Settings

logger = logging.getLogger(__name__)


def _get_gemini_llm(settings: Settings) -> LLM:
    """Create Gemini LLM for content tasks."""
    return LLM(
        model=f"gemini/{settings.gemini_model}",
        temperature=0.7,
        timeout=settings.request_timeout_seconds
    )


def _get_perplexity_llm(settings: Settings) -> LLM:
    """Create Perplexity LLM for research tasks."""
    return LLM(
        model=f"perplexity/{settings.perplexity_model}",
        temperature=0.5,
        timeout=settings.request_timeout_seconds
    )


class SocialMediaCrew:
    """Social Media Content Automation Hub crew with 4 specialized agents."""
    
    def __init__(self):
        self.settings = get_settings()
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    def _execute_crew(self, crew: Crew) -> str:
        """Execute the crew with retry logic."""
        result = crew.kickoff()
        return result.raw if hasattr(result, 'raw') else str(result)
    
    def run(self, payload: dict, meta: dict | None, trace_id: str) -> dict:
        """
        Run the Social Media crew workflow.
        
        Args:
            payload: Must contain 'industry' and 'company_name'
            meta: Optional metadata (not used for this crew)
            trace_id: Trace ID for logging
            
        Returns:
            dict with execution result
        """
        # Validate required fields
        if "industry" not in payload:
            raise ValueError("payload must contain 'industry' field")
        if "company_name" not in payload:
            raise ValueError("payload must contain 'company_name' field")
        
        industry = payload["industry"]
        company_name = payload["company_name"]
        
        # Get LLMs
        gemini_llm = _get_gemini_llm(self.settings)
        research_llm = _get_perplexity_llm(self.settings)
        
        # Create agents
        research_agent = Agent(
            role="Social Media Trend Research Specialist",
            goal=f"Research and identify trending topics, hashtags, and content opportunities in {industry}",
            backstory="""You are an expert social media researcher with deep knowledge of digital 
            marketing trends and viral content patterns. You understand the nuances of different 
            social media platforms and how trends translate across them.""",
            llm=research_llm,
            allow_delegation=False,
            verbose=True
        )
        
        content_agent = Agent(
            role="Content Strategy and Creation Specialist",
            goal=f"Generate compelling, platform-specific social media content ideas for {company_name}",
            backstory="""You are a creative social media strategist with expertise in content 
            creation across all major platforms. You excel at adapting trending topics into 
            brand-appropriate content that drives engagement.""",
            llm=gemini_llm,
            allow_delegation=False,
            verbose=True
        )
        
        analytics_agent = Agent(
            role="Engagement Analytics and Optimization Specialist",
            goal=f"Analyze social media performance and provide data-driven recommendations for {company_name}",
            backstory="""You are a social media analytics expert with extensive experience in 
            interpreting engagement metrics. You excel at finding patterns in posting times, 
            content performance, and audience behavior.""",
            llm=gemini_llm,
            allow_delegation=False,
            verbose=True
        )
        
        scheduler_agent = Agent(
            role="Social Media Schedule Coordinator",
            goal=f"Create comprehensive posting schedules optimizing timing and frequency for {company_name}",
            backstory="""You are an experienced social media manager who specializes in content 
            scheduling and campaign coordination. You understand optimal posting frequencies 
            for different platforms and time zone considerations.""",
            llm=gemini_llm,
            allow_delegation=False,
            verbose=True
        )
        
        # Define tasks
        research_task = Task(
            description=f"""Research current trending topics, hashtags, and conversation themes 
            relevant to the {industry} industry. Identify emerging trends, viral content patterns, 
            and topics that are gaining traction. Focus on finding opportunities that {company_name} 
            can leverage for engaging content.""",
            expected_output=f"""A comprehensive trend report including:
            1) Top 10 trending topics in {industry}
            2) Relevant hashtags and their performance
            3) Emerging conversation themes
            4) Content opportunities for {company_name}
            5) Platform-specific trending patterns""",
            agent=research_agent
        )
        
        analytics_task = Task(
            description=f"""Analyze current social media performance patterns and industry best 
            practices to identify optimal posting times, content types, and engagement strategies 
            for {company_name}. Provide data-driven recommendations.""",
            expected_output="""A performance optimization report including:
            1) Optimal posting times for each platform
            2) Best performing content types and formats
            3) Audience engagement patterns
            4) Posting frequency recommendations
            5) Key metrics to track""",
            agent=analytics_agent
        )
        
        content_task = Task(
            description=f"""Based on the trending topics research, create a comprehensive content 
            strategy with specific post ideas, captions, and content formats optimized for 
            different social media platforms. Ensure all content aligns with {company_name}'s 
            brand voice while leveraging current trends.""",
            expected_output="""A detailed content strategy including:
            1) 20+ specific post ideas with platform adaptations
            2) Sample captions for each platform
            3) Content themes and pillars
            4) Visual content suggestions
            5) Hashtag recommendations
            6) Call-to-action strategies""",
            agent=content_agent,
            context=[research_task]
        )
        
        schedule_task = Task(
            description=f"""Combine the content strategy and optimal timing recommendations to 
            create a comprehensive 30-day social media publishing schedule for {company_name}. 
            Include specific posting times, platform assignments, and content details.""",
            expected_output="""A complete 30-day social media calendar including:
            1) Daily posting schedule with specific times
            2) Content assignments with captions
            3) Visual content requirements
            4) Cross-platform adaptation notes
            5) Engagement monitoring checkpoints
            6) Content preparation timeline""",
            agent=scheduler_agent,
            context=[content_task, analytics_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[research_agent, content_agent, analytics_agent, scheduler_agent],
            tasks=[research_task, analytics_task, content_task, schedule_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info(f"Starting Social Media crew for {company_name} in {industry}")
        
        result = self._execute_crew(crew)
        
        return {
            "workflow": "social_media",
            "output": result,
            "input_summary": {
                "industry": industry,
                "company_name": company_name
            }
        }

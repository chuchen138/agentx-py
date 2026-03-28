from typing import List, Dict, Any, Optional
from langchain.agents import AgentType, initialize_agent
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

class LangChainAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def create_agent(self, system_prompt: str, tools: List[BaseTool], model_name: str = "gpt-4") -> Any:
        llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=model_name,
            temperature=0.7
        )
        
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            system_message=system_prompt,
            verbose=True
        )
        
        return agent
    
    def create_tool(self, name: str, description: str, func: callable) -> BaseTool:
        from langchain.tools import Tool
        return Tool(
            name=name,
            func=func,
            description=description
        )
    
    def run_agent(self, agent: Any, prompt: str) -> str:
        return agent.run(prompt)
    
    def create_chain(self, prompt_template: str, model_name: str = "gpt-4") -> Any:
        llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=model_name,
            temperature=0.7
        )
        
        prompt = PromptTemplate(
            input_variables=["input"],
            template=prompt_template
        )
        
        from langchain.chains import LLMChain
        return LLMChain(llm=llm, prompt=prompt)
    
    def run_chain(self, chain: Any, input_data: Dict[str, Any]) -> str:
        return chain.run(input_data)

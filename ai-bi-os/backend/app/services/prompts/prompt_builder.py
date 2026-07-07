from jinja2 import Template
from app.models.context import ContextPackage
from app.models.prompt import PromptTemplate, PromptPackage

class PromptBuilder:
    """Injects the ContextPackage into Jinja2 templates."""
    
    @staticmethod
    def build(context_package: ContextPackage, template: PromptTemplate) -> PromptPackage:
        # 1. Prepare Jinja2 Variables
        variables = {
            "question": context_package.question,
            "context_items": [item.content for item in context_package.items],
            "business_domain": context_package.business_domain,
            "output_schema": template.output_schema
        }
        
        # 2. Render templates
        sys_template = Template(template.system_template)
        system_prompt = sys_template.render(**variables)
        
        usr_template = Template(template.user_template)
        user_prompt = usr_template.render(**variables)
        
        # 3. Create Package
        package = PromptPackage(
            context_package_id=context_package.id,
            template_id=template.id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=template.output_schema
        )
        
        # Heuristic token estimate for the prompt strings
        package.estimated_tokens = (len(system_prompt) + len(user_prompt)) // 4
        
        return package

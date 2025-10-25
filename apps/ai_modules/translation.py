from modeltranslation.translator import translator, TranslationOptions
from .models import AIModule, AIModuleDetail

class AIModuleTranslationOptions(TranslationOptions):
    fields = ('name', 'task_short_description')

class AIModuleDetailTranslationOptions(TranslationOptions):
    fields = ('description', 'technical_info')

translator.register(AIModule, AIModuleTranslationOptions)
translator.register(AIModuleDetail, AIModuleDetailTranslationOptions)

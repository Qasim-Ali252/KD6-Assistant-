import json
import os
from pathlib import Path

class Live2DModel:
    """Loader for Live2D Cubism model files"""
    
    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.model_dir = self.model_path.parent
        self.model_data = None
        self.textures = []
        self.expressions = {}
        self.motions = {}
        
        self._load_model()
    
    def _load_model(self):
        """Load the model3.json file"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        with open(self.model_path, 'r', encoding='utf-8') as f:
            self.model_data = json.load(f)
        
        print(f"Loaded Live2D model: {self.model_path.name}")
        
        # Load textures
        self._load_textures()
        
        # Load expressions
        self._load_expressions()
        
        # Load motions
        self._load_motions()
    
    def _load_textures(self):
        """Load texture file paths"""
        if 'FileReferences' in self.model_data:
            textures_data = self.model_data['FileReferences'].get('Textures', [])
            for texture_path in textures_data:
                full_path = self.model_dir / texture_path
                if full_path.exists():
                    self.textures.append(str(full_path))
                    print(f"  Texture: {texture_path}")
    
    def _load_expressions(self):
        """Load expression files"""
        if 'FileReferences' in self.model_data:
            expressions_data = self.model_data['FileReferences'].get('Expressions', [])
            for exp_data in expressions_data:
                name = exp_data.get('Name', '')
                file_path = exp_data.get('File', '')
                full_path = self.model_dir / file_path
                
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        self.expressions[name] = json.load(f)
                    print(f"  Expression: {name}")
    
    def _load_motions(self):
        """Load motion files"""
        if 'FileReferences' in self.model_data:
            motions_data = self.model_data['FileReferences'].get('Motions', {})
            for category, motion_list in motions_data.items():
                self.motions[category] = []
                for motion_data in motion_list:
                    file_path = motion_data.get('File', '')
                    full_path = self.model_dir / file_path
                    
                    if full_path.exists():
                        self.motions[category].append(str(full_path))
                        print(f"  Motion ({category}): {file_path}")
    
    def get_texture_path(self, index=0):
        """Get texture file path"""
        if index < len(self.textures):
            return self.textures[index]
        return None
    
    def get_expression_names(self):
        """Get list of available expressions"""
        return list(self.expressions.keys())
    
    def get_motion_categories(self):
        """Get list of motion categories"""
        return list(self.motions.keys())

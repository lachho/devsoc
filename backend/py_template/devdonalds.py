from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
    name: str

@dataclass
class RequiredItem():
    name: str
    quantity: int

@dataclass
class Recipe(CookbookEntry):
    required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
    cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
    data = request.get_json()
    recipe_name = data.get('input', '')
    parsed_name = parse_handwriting(recipe_name)
    if parsed_name is None:
        return 'Invalid recipe name', 400
    return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
    if not recipeName or len(recipeName) <= 0:
        return None

    recipeName = recipeName.replace('-', ' ').replace('_', ' ')
    recipeName = re.sub(r'[^a-zA-Z ]', '', recipeName)

    words = recipeName.split()
    cleanedWords = [word.capitalize() for word in words]
    return " ".join(cleanedWords)

# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    

    entryData = request.get_json()
    if 'name' not in entryData or 'type' not in entryData:
        return jsonify({'error': 'Required fields not present'}), 400

    entryType = entryData['type']

    if entryType not in ["ingredient", "recipe"]:
        return jsonify({"error": "Invalid entry type"}), 400
    
    if (entryData['name'] in cookbook):
        return jsonify({'error': 'Entry already exists'}), 400
    
    if entryType == 'ingredient':
        if 'cookTime' not in entryData \
            or not isinstance(entryData['cookTime'], int) \
            or entryData['cookTime'] < 0:
            return jsonify({'error': 'Cook Time must be a non-negative number'}), 400
        
        cookbook[entryData['name']] = {"type": entryType, "cookTime": entryData['cookTime']}
    
    elif entryType == 'recipe':
        if 'requiredItems' not in entryData \
            or not isinstance(entryData['requiredItems'], list):
            return jsonify({'error': 'Required Items must be a list of ingredients'}), 400
        
        requiredItem = {}
        for item in entryData['requiredItems']:
            if 'name' not in item \
                or 'quantity' not in item \
                or not isinstance(item['quantity'], int) \
                or item['quantity'] <= 0:
                return jsonify({'error': 'Required items must have a unique name and positive integer quantity'}), 400
            
            if item['name'] in requiredItem:
                return jsonify({"error": "Each required item can only appear once per recipe"}), 400
            
            requiredItem[item['name']] = item['quantity']
        cookbook[entryData['name']] = {"type": entryType, "requiredItems": requiredItem}
    
    return jsonify({}), 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
def writeRecipe(recipe, totalIngredients, cookTime, multiplier=1):
    if recipe not in cookbook:
        return 0, "Item not found in cookbook"
    for item, quantity in cookbook[recipe]['requiredItems'].items():
        if item not in cookbook:
            return 0, "Item not found in cookbook"
        
        totalQuantity = quantity * multiplier
        if cookbook[item]['type'] == 'ingredient':
            cookTime += cookbook[item]['cookTime'] * totalQuantity
            totalIngredients[item] = totalQuantity + totalIngredients.get(item, 0)
        elif cookbook[item]['type'] == 'recipe':
            cookTime, error = writeRecipe(item, totalIngredients, cookTime, totalQuantity)
            if error:
                return 0, error
    return cookTime, None
        
@app.route('/summary', methods=['GET'])
def summary():
    name = request.args.get("name")

    if (not name or not isinstance(name, str)):
        return jsonify({'error': 'Name is required'}), 400
    
    if (name not in cookbook or cookbook[name]['type'] != 'recipe'):
        return jsonify({'error': 'Recipe not found in cookbook'}), 400

    cookTime = 0
    totalIngredients = {}
    cookTime, error = writeRecipe(name, totalIngredients, cookTime)

    if error:
        return jsonify({'error': error}), 400

    ingredients = [{'name': item, 'quantity': totalIngredients[item]} for item in totalIngredients]
    return jsonify({"name": name, "cookTime": cookTime, "ingredients": ingredients}), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=8080)

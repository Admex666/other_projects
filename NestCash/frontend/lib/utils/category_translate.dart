class CategoryTranslate {

static String getLocalizedCategory(String category) {
    switch (category.toLowerCase()) {
      case 'élelmiszer':
      case 'food':
        return 'category_food';
      case 'lakhatás':
      case 'housing':
        return 'category_housing';
      case 'közlekedés':
      case 'transport':
        return 'category_transport';
      case 'traveling':
      case 'utazás':
        return 'category_traveling';
      case 'szórakozás':
      case 'entertainment':
        return 'category_entertainment';
      case 'ruházat':
      case 'clothing':
        return 'category_clothing';
      case 'egészségügy':
      case 'healthcare':
        return 'category_healthcare';
      case 'háztartási cikkek':
      case 'household goods':
        return 'category_household_goods';
      case 'kommunikáció':
      case 'communication':
        return 'category_communication';
      case 'szolgáltatások':
      case 'services':
        return 'category_communication';
      case 'oktatás':
      case 'education':
        return 'category_education';
      case 'ajándék':
      case 'ajándékok':
      case 'gifts':
        return 'category_gifts';
      case 'fizetés':
      case 'salary':
        return 'category_salary';
      case 'egyéb bevétel':
      case 'other income':
        return 'category_otherincome';
      case 'befektetés':
      case 'investment':
        return 'category_investment';
      case 'eladás':
      case 'sale':
        return 'category_sale';
      case 'egyéb':
      case 'other':
        return 'category_other';
      default:
        return category;
    }
  }

  static String getLocalizedGoal(String goal) {
    switch (goal.toLowerCase()) {
      case 'pénzügyek':
      case 'financial':
        return 'accpart_model.goal_category.financial';
      case 'megtakarítás':
      case 'savings':
        return 'accpart_model.goal_category.savings';
      case 'befektetés':
      case 'investment':
        return 'accpart_model.goal_category.investment';
      case 'kiadások kontroll':
      case 'spending control':
        return 'accpart_model.goal_category.spending_control';
      case 'szokásépítés':
      case 'habit building':
        return 'accpart_model.goal_category.habit_building';
      default:
        return goal;
    }
  }

}
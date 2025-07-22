// lib/screens/manage_categories_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/category_service.dart';
import 'package:frontend/models/category.dart';

class ManageCategoriesScreen extends StatefulWidget {
  final String userId;

  const ManageCategoriesScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _ManageCategoriesScreenState createState() => _ManageCategoriesScreenState();
}

class _ManageCategoriesScreenState extends State<ManageCategoriesScreen> {
  final CategoryService _categoryService = CategoryService();
  final _formKey = GlobalKey<FormState>();
  final _categoryNameController = TextEditingController();
  String _selectedType = 'expense';
  List<Category> _categories = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    setState(() {
      _isLoading = true;
    });
    
    try {
      final categories = await _categoryService.getCategories();
      setState(() {
        _categories = categories;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kategóriák betöltésekor: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showAddCategoryDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Új kategória hozzáadása'),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _categoryNameController,
                decoration: InputDecoration(labelText: 'Kategória neve'),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Kérjük, adjon meg egy nevet';
                  }
                  return null;
                },
              ),
              SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedType,
                items: [
                  DropdownMenuItem(
                    value: 'expense',
                    child: Text('Kiadás'),
                  ),
                  DropdownMenuItem(
                    value: 'income',
                    child: Text('Bevétel'),
                  ),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedType = value!;
                  });
                },
                decoration: InputDecoration(labelText: 'Típus'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Mégse')),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _addCategory();
                Navigator.pop(context);
              }
            },
            child: Text('Hozzáadás'),
          ),
        ],
      ),
    );
  }

  Future<void> _addCategory() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      await _categoryService.createCategory(
        _categoryNameController.text,
        _selectedType,
      );
      _categoryNameController.clear();
      await _loadCategories();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Kategória sikeresen hozzáadva!'),
          backgroundColor: Colors.green,),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kategória hozzáadásakor: $e')),
      );
    }
  }

  Future<void> _deleteCategory(String categoryId) async {
    // Megerősítő dialógus megjelenítése
    bool? shouldDelete = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Kategória törlése'),
          content: Text('Biztosan törölni szeretnéd ezt a kategóriát?'),
          actions: <Widget>[
            TextButton(
              child: Text('Mégse'),
              onPressed: () => Navigator.of(context).pop(false),
            ),
            TextButton(
              child: Text('Törlés', style: TextStyle(color: Colors.red)),
              onPressed: () => Navigator.of(context).pop(true),
            ),
          ],
        );
      },
    );

    if (shouldDelete != true) return;

    try {
      await _categoryService.deleteCategory(categoryId);
      await _loadCategories();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Kategória sikeresen törölve!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hiba a kategória törlésekor: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Container(
          decoration: BoxDecoration(
            // Gradiens háttér, mint a Dashboard tetején
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF00D4A3), // A Dashboard tetejének színe
                Color(0xFFE8F6F3), // A Dashboard aljának színe
              ],
              stops: [0.0, 0.4],
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.max, // A Column kitölti a rendelkezésre álló magasságot
            children: [
              // Header rész (ez marad a gradiens háttéren)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back, color: Colors.black87),
                      onPressed: () {
                        Navigator.pop(context);
                      },
                    ),
                    Expanded(
                      child: Text(
                        'Kategóriák Kezelése',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    // Átlátszó IconButton a jobb oldalon a vizuális középre igazításért
                    Opacity(
                      opacity: 0.0, // Láthatatlanná teszi a widgetet
                      child: IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.transparent), // Átlátszó ikon
                        onPressed: () {}, // Üres onPressed, nincs funkcionalitása
                      ),
                    ),
                  ],
                ),
              ),

              // Content Container (ez lesz a fehér, lekerekített sarkú rész)
              Expanded( // Expanded-be tesszük, hogy kitöltse a maradék helyet
                child: Container(
                  margin: EdgeInsets.symmetric(horizontal: 0), // Eltávolítjuk a margin-t
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5), // Fehér vagy világosszürke háttér
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(height: 16),

                        // Gombok
                        Container(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton.icon(
                            onPressed: _loadCategories,
                            icon: Icon(Icons.refresh, color: Colors.white),
                            label: Text(
                              'Kategóriák frissítése',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFF00D4AA),
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),

                        SizedBox(height: 12),

                        Container(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton.icon(
                            onPressed: _showAddCategoryDialog,
                            icon: Icon(Icons.add, color: Colors.white),
                            label: Text(
                              'Új kategória',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.green,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),

                        SizedBox(height: 24),

                        // Tartalom megjelenítése
                        if (_isLoading)
                          Expanded(
                            child: Center(
                              child: CircularProgressIndicator(
                                color: Color(0xFF00D4AA),
                              ),
                            ),
                          )
                        else
                          Expanded(
                            child: ListView.builder(
                              itemCount: _categories.length,
                              itemBuilder: (context, index) {
                                final category = _categories[index];
                                return Container(
                                  margin: EdgeInsets.only(bottom: 12),
                                  decoration: BoxDecoration(
                                    color: category.type == 'income' 
                                        ? Color(0xFFE8F5E8) 
                                        : Color(0xFFFFF2F2),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: ListTile(
                                    title: Text(
                                      category.name,
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w500,
                                        color: Colors.black87,
                                      ),
                                    ),
                                    subtitle: Text(
                                      category.type == 'income' ? 'Bevétel' : 'Kiadás',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.black54,
                                      ),
                                    ),
                                    leading: Container(
                                      padding: EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: category.type == 'income' 
                                            ? Colors.green.withOpacity(0.2) 
                                            : Colors.red.withOpacity(0.2),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Icon(
                                        category.type == 'income' 
                                            ? Icons.arrow_upward 
                                            : Icons.arrow_downward,
                                        color: category.type == 'income' 
                                            ? Colors.green 
                                            : Colors.red,
                                        size: 20,
                                      ),
                                    ),
                                    trailing: IconButton(
                                      icon: Icon(Icons.delete, color: Colors.red),
                                      onPressed: () => _deleteCategory(category.id),
                                    ),
                                    contentPadding: EdgeInsets.symmetric(
                                      horizontal: 16, 
                                      vertical: 8
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
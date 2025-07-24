// lib/screens/forum/create_post_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/forum_service.dart';
import 'package:frontend/models/forum_models.dart';

class CreatePostScreen extends StatefulWidget {
  @override
  _CreatePostScreenState createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends State<CreatePostScreen> {
  final ForumService _forumService = ForumService();
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  
  PostCategory _selectedCategory = PostCategory.general;
  String _selectedPrivacyLevel = 'public';
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  Future<void> _createPost() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      await _forumService.createPost(
        title: _titleController.text.trim(),
        content: _contentController.text.trim(),
        category: _selectedCategory.value,
        privacyLevel: _selectedPrivacyLevel,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Poszt sikeresen létrehozva!'),
          backgroundColor: Colors.green,
        ),
      );

      Navigator.pop(context, true); // Return true to indicate success
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hiba a poszt létrehozásakor: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF00D4A3),
                Color(0xFFE8F6F3),
              ],
              stops: [0.0, 0.4],
            ),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.arrow_back, color: Colors.black87),
                      onPressed: () => Navigator.pop(context),
                    ),
                    Expanded(
                      child: Text(
                        'Új poszt létrehozása',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    TextButton(
                      onPressed: _isLoading ? null : _createPost,
                      child: Text(
                        'Közzététel',
                        style: TextStyle(
                          color: _isLoading ? Colors.grey : Colors.black87,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Content area
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: Form(
                    key: _formKey,
                    child: ListView(
                      padding: EdgeInsets.all(24),
                      children: [
                        // Title field
                        Text(
                          'Cím',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 8),
                        TextFormField(
                          controller: _titleController,
                          decoration: InputDecoration(
                            hintText: 'Add meg a poszt címét...',
                            filled: true,
                            fillColor: Colors.white,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide.none,
                            ),
                            contentPadding: EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 12,
                            ),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'A cím megadása kötelező';
                            }
                            if (value.trim().length < 3) {
                              return 'A cím legalább 3 karakter hosszú legyen';
                            }
                            if (value.trim().length > 200) {
                              return 'A cím maximum 200 karakter hosszú lehet';
                            }
                            return null;
                          },
                        ),

                        SizedBox(height: 24),

                        // Category selection
                        Text(
                          'Kategória',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 8),
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: DropdownButtonFormField<PostCategory>(
                            value: _selectedCategory,
                            decoration: InputDecoration(
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                            ),
                            items: PostCategory.values.map((category) {
                              return DropdownMenuItem(
                                value: category,
                                child: Text(category.displayName),
                              );
                            }).toList(),
                            onChanged: (value) {
                              setState(() {
                                _selectedCategory = value!;
                              });
                            },
                          ),
                        ),

                        SizedBox(height: 24),

                        // Privacy level selection
                        Text(
                          'Láthatóság',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 8),
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: DropdownButtonFormField<String>(
                            value: _selectedPrivacyLevel,
                            decoration: InputDecoration(
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                            ),
                            items: [
                              DropdownMenuItem(
                                value: 'public',
                                child: Row(
                                  children: [
                                    Icon(Icons.public, size: 20, color: Colors.green),
                                    SizedBox(width: 8),
                                    Text('Nyilvános'),
                                  ],
                                ),
                              ),
                              DropdownMenuItem(
                                value: 'friends',
                                child: Row(
                                  children: [
                                    Icon(Icons.group, size: 20, color: Colors.orange),
                                    SizedBox(width: 8),
                                    Text('Csak követők'),
                                  ],
                                ),
                              ),
                              DropdownMenuItem(
                                value: 'private',
                                child: Row(
                                  children: [
                                    Icon(Icons.lock, size: 20, color: Colors.red),
                                    SizedBox(width: 8),
                                    Text('Privát'),
                                  ],
                                ),
                              ),
                            ],
                            onChanged: (value) {
                              setState(() {
                                _selectedPrivacyLevel = value!;
                              });
                            },
                          ),
                        ),

                        SizedBox(height: 24),

                        // Content field
                        Text(
                          'Tartalom',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 8),
                        TextFormField(
                          controller: _contentController,
                          maxLines: 12,
                          decoration: InputDecoration(
                            hintText: 'Írd le, amit szeretnél megosztani...',
                            filled: true,
                            fillColor: Colors.white,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide.none,
                            ),
                            contentPadding: EdgeInsets.all(16),
                            alignLabelWithHint: true,
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'A tartalom megadása kötelező';
                            }
                            if (value.trim().length < 10) {
                              return 'A tartalom legalább 10 karakter hosszú legyen';
                            }
                            if (value.trim().length > 5000) {
                              return 'A tartalom maximum 5000 karakter hosszú lehet';
                            }
                            return null;
                          },
                        ),

                        SizedBox(height: 32),

                        // Create button
                        Container(
                          width: double.infinity,
                          height: 50,
                          child: ElevatedButton(
                            onPressed: _isLoading ? null : _createPost,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFF00D4AA),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 0,
                            ),
                            child: _isLoading
                                ? SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      color: Colors.white,
                                      strokeWidth: 2,
                                    ),
                                  )
                                : Text(
                                    'Poszt közzététele',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                          ),
                        ),

                        SizedBox(height: 16),

                        // Helper text
                        Container(
                          padding: EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(Icons.info_outline, color: Colors.blue, size: 20),
                                  SizedBox(width: 8),
                                  Text(
                                    'Tippek',
                                    style: TextStyle(
                                      color: Colors.blue,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              SizedBox(height: 8),
                              Text(
                                '• Válaszd ki a megfelelő kategóriát a jobb láthatóság érdekében\n'
                                '• Írj informatív címet, ami tükrözi a poszt tartalmát\n'
                                '• A tisztelettudó kommunikáció mindenkinek jó',
                                style: TextStyle(
                                  color: Colors.blue[700],
                                  fontSize: 14,
                                  height: 1.4,
                                ),
                              ),
                            ],
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
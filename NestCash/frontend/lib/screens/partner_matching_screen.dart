// lib/screens/partner_matching_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/accountability_models.dart';
import '../providers/accountability_provider.dart';
import '../providers/subscription_provider.dart';
import '../widgets/swipeable_card.dart';

class PartnerMatchingScreen extends StatefulWidget {
  const PartnerMatchingScreen({Key? key}) : super(key: key);

  @override
  _PartnerMatchingScreenState createState() => _PartnerMatchingScreenState();
}

class _PartnerMatchingScreenState extends State<PartnerMatchingScreen> {
  List<PartnerSuggestion> _suggestions = [];
  int _currentIndex = 0;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSuggestions();
  }

  Future<void> _loadSuggestions() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final subscriptionProvider = Provider.of<SubscriptionProvider>(context, listen: false);
      
      // Check if user has access to matching
      if (!subscriptionProvider.isPlusOrHigher) {
        setState(() {
          _error = 'Matching funkció csak Plus és Pro előfizetőknek elérhető';
          _isLoading = false;
        });
        return;
      }

      final accountabilityProvider = Provider.of<AccountabilityProvider>(context, listen: false);
      await accountabilityProvider.loadPartnerSuggestions(limit: 20);
      
      setState(() {
        _suggestions = accountabilityProvider.suggestions;
        _currentIndex = 0;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _onSwipeLeft() {
    // Dislike - move to next card
    _nextCard();
  }

  void _onSwipeRight() {
    // Like - send partnership request
    if (_currentIndex < _suggestions.length) {
      _sendPartnershipRequest(_suggestions[_currentIndex]);
    }
    _nextCard();
  }

  void _nextCard() {
    setState(() {
      _currentIndex++;
    });
  }

  Future<void> _sendPartnershipRequest(PartnerSuggestion suggestion) async {
    try {
      final accountabilityProvider = Provider.of<AccountabilityProvider>(context, listen: false);
      
      // Show dialog to configure the request
      final result = await showDialog<Map<String, dynamic>>(
        context: context,
        builder: (context) => _PartnershipRequestDialog(suggestion: suggestion),
      );

      if (result != null) {
        final request = PartnershipRequest(
          targetUserId: suggestion.userId,
          checkinFrequency: result['frequency'],
          sharedGoals: result['goals'],
          message: result['message'],
        );

        final success = await accountabilityProvider.sendPartnershipRequest(request);
        
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Partnership kérelem elküldve ${suggestion.username} felhasználónak!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hiba: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: Icon(Icons.arrow_back, color: Colors.black87, size: 24),
                  ),
                  Expanded(
                    child: Text(
                      'Partner keresés',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  IconButton(
                    onPressed: _loadSuggestions,
                    icon: Icon(Icons.refresh, color: Colors.black87, size: 24),
                  ),
                ],
              ),
            ),

            // Content
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: _buildContent(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Color(0xFF00D4AA)),
            SizedBox(height: 16),
            Text(
              'Partner javaslatok betöltése...',
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.grey[400],
              ),
              SizedBox(height: 16),
              Text(
                'Hiba történt',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[600],
                ),
              ),
              SizedBox(height: 8),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.grey[500],
                ),
              ),
              SizedBox(height: 24),
              ElevatedButton(
                onPressed: _loadSuggestions,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Color(0xFF00D4AA),
                  foregroundColor: Colors.white,
                ),
                child: Text('Újrapróbálás'),
              ),
            ],
          ),
        ),
      );
    }

    if (_currentIndex >= _suggestions.length) {
      return Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.check_circle_outline,
                size: 64,
                color: Colors.green,
              ),
              SizedBox(height: 16),
              Text(
                'Minden javaslatot megnéztél!',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[600],
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Próbálkozz újra később új javaslatok eléréséhez.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.grey[500],
                ),
              ),
              SizedBox(height: 24),
              ElevatedButton(
                onPressed: _loadSuggestions,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Color(0xFF00D4AA),
                  foregroundColor: Colors.white,
                ),
                child: Text('Új javaslatok'),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: [
        // Cards stack
        Expanded(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: Stack(
              children: [
                // Background cards (next 2-3 cards)
                for (int i = _currentIndex + 2; i >= _currentIndex; i--)
                  if (i < _suggestions.length)
                    Positioned(
                      top: (i - _currentIndex) * 8.0,
                      left: (i - _currentIndex) * 4.0,
                      right: (i - _currentIndex) * 4.0,
                      bottom: 0,
                      child: SwipeableCard(
                        suggestion: _suggestions[i],
                        isTopCard: i == _currentIndex,
                        onSwipeLeft: i == _currentIndex ? _onSwipeLeft : null,
                        onSwipeRight: i == _currentIndex ? _onSwipeRight : null,
                      ),
                    ),
              ],
            ),
          ),
        ),

        // Action buttons
        Padding(
          padding: EdgeInsets.all(24),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Dislike button
              GestureDetector(
                onTap: _onSwipeLeft,
                child: Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 10,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Icon(
                    Icons.close,
                    color: Colors.red,
                    size: 32,
                  ),
                ),
              ),

              // Like button
              GestureDetector(
                onTap: _onSwipeRight,
                child: Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: Color(0xFF00D4AA),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 10,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Icon(
                    Icons.favorite,
                    color: Colors.white,
                    size: 32,
                  ),
                ),
              ),
            ],
          ),
        ),

        // Progress indicator
        Container(
          padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: LinearProgressIndicator(
            value: _suggestions.isNotEmpty ? (_currentIndex + 1) / _suggestions.length : 0,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4AA)),
            minHeight: 4,
          ),
        ),
      ],
    );
  }
}

class _PartnershipRequestDialog extends StatefulWidget {
  final PartnerSuggestion suggestion;

  const _PartnershipRequestDialog({required this.suggestion});

  @override
  _PartnershipRequestDialogState createState() => _PartnershipRequestDialogState();
}

class _PartnershipRequestDialogState extends State<_PartnershipRequestDialog> {
  CheckInFrequency _frequency = CheckInFrequency.weekly;
  List<String> _selectedGoals = [];
  final TextEditingController _messageController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _selectedGoals = List.from(widget.suggestion.commonGoals);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Partnership kérelem'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Partner: ${widget.suggestion.username}'),
            SizedBox(height: 16),
            
            Text('Check-in gyakoriság:', style: TextStyle(fontWeight: FontWeight.bold)),
            DropdownButton<CheckInFrequency>(
              value: _frequency,
              isExpanded: true,
              onChanged: (frequency) {
                setState(() {
                  _frequency = frequency!;
                });
              },
              items: CheckInFrequency.values.map((freq) {
                return DropdownMenuItem(
                  value: freq,
                  child: Text(freq.displayName),
                );
              }).toList(),
            ),
            
            SizedBox(height: 16),
            Text('Közös célok:', style: TextStyle(fontWeight: FontWeight.bold)),
            ...widget.suggestion.commonGoals.map((goal) {
              return CheckboxListTile(
                title: Text(goal),
                value: _selectedGoals.contains(goal),
                onChanged: (checked) {
                  setState(() {
                    if (checked!) {
                      _selectedGoals.add(goal);
                    } else {
                      _selectedGoals.remove(goal);
                    }
                  });
                },
              );
            }).toList(),
            
            SizedBox(height: 16),
            Text('Üzenet (opcionális):', style: TextStyle(fontWeight: FontWeight.bold)),
            TextField(
              controller: _messageController,
              maxLines: 3,
              decoration: InputDecoration(
                hintText: 'Írj egy rövid bemutatkozó üzenetet...',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Mégse'),
        ),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context, {
              'frequency': _frequency,
              'goals': _selectedGoals,
              'message': _messageController.text.isNotEmpty ? _messageController.text : null,
            });
          },
          child: Text('Küldés'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }
}
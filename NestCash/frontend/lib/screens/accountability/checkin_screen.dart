// lib/screens/accountability/checkin_screen.dart

import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:provider/provider.dart';
import 'package:frontend/models/accountability_models.dart';
import 'package:frontend/providers/accountability_provider.dart';
import 'package:frontend/services/auth_service.dart';

class CheckInScreen extends StatefulWidget {
  final String partnershipId;
  final String partnerName;

  const CheckInScreen({
    Key? key,
    required this.partnershipId,
    required this.partnerName,
  }) : super(key: key);

  @override
  _CheckInScreenState createState() => _CheckInScreenState();
}

class _CheckInScreenState extends State<CheckInScreen> {
  bool _goalsMet = true;
  int _progressRating = 3;
  final TextEditingController _notesController = TextEditingController();
  bool _isSubmitting = false;

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
                    child: Column(
                      children: [
                        Text(
                          'checkin_title'.tr(),
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        Text(
                          'checkin_partner'.tr(namedArgs: {'partnerName': widget.partnerName}),
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.black54,
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(width: 48), // Balance the back button
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
                child: SingleChildScrollView(
                  padding: EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Date
                      Container(
                        width: double.infinity,
                        padding: EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              blurRadius: 10,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.today,
                              color: Color(0xFF00D4AA),
                              size: 24,
                            ),
                            SizedBox(width: 12),
                            Text(
                              'today_checkin'.tr(namedArgs: {'date': DateFormat.yMd().format(DateTime.now())}),
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                      ),

                      SizedBox(height: 24),

                      // Goals met question
                      Container(
                        width: double.infinity,
                        padding: EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              blurRadius: 10,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'goals_met_question'.tr(),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 16),
                            Row(
                              children: [
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () => setState(() => _goalsMet = true),
                                    child: Container(
                                      padding: EdgeInsets.all(16),
                                      decoration: BoxDecoration(
                                        color: _goalsMet ? Colors.green : Colors.grey[100],
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                          color: _goalsMet ? Colors.green : Colors.grey[300]!,
                                          width: 2,
                                        ),
                                      ),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Icon(
                                            Icons.check_circle,
                                            color: _goalsMet ? Colors.white : Colors.grey[600],
                                            size: 20,
                                          ),
                                          SizedBox(width: 8),
                                          Text(
                                            'yes'.tr(),
                                            style: TextStyle(
                                              color: _goalsMet ? Colors.white : Colors.grey[600],
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                                SizedBox(width: 12),
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () => setState(() => _goalsMet = false),
                                    child: Container(
                                      padding: EdgeInsets.all(16),
                                      decoration: BoxDecoration(
                                        color: !_goalsMet ? Colors.red : Colors.grey[100],
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                          color: !_goalsMet ? Colors.red : Colors.grey[300]!,
                                          width: 2,
                                        ),
                                      ),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Icon(
                                            Icons.cancel,
                                            color: !_goalsMet ? Colors.white : Colors.grey[600],
                                            size: 20,
                                          ),
                                          SizedBox(width: 8),
                                          Text(
                                            'no'.tr(),
                                            style: TextStyle(
                                              color: !_goalsMet ? Colors.white : Colors.grey[600],
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),

                      SizedBox(height: 24),

                      // Progress rating
                      Container(
                        width: double.infinity,
                        padding: EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              blurRadius: 10,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'progress_rating_question'.tr(),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              '1 - ${'rating_1'.tr()}\n5 - ${'rating_5'.tr()}',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 14,
                              ),
                            ),
                            SizedBox(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                              children: List.generate(5, (index) {
                                final rating = index + 1;
                                final isSelected = _progressRating == rating;
                                
                                return GestureDetector(
                                  onTap: () => setState(() => _progressRating = rating),
                                  child: Container(
                                    width: 50,
                                    height: 50,
                                    decoration: BoxDecoration(
                                      color: isSelected ? Color(0xFF00D4AA) : Colors.grey[100],
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                        color: isSelected ? Color(0xFF00D4AA) : Colors.grey[300]!,
                                        width: 2,
                                      ),
                                    ),
                                    child: Center(
                                      child: Text(
                                        rating.toString(),
                                        style: TextStyle(
                                          fontSize: 20,
                                          fontWeight: FontWeight.bold,
                                          color: isSelected ? Colors.white : Colors.grey[600],
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              }),
                            ),
                            SizedBox(height: 16),
                          ],
                        ),
                      ),

                      SizedBox(height: 24),

                      // Notes
                      Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              blurRadius: 10,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Padding(
                              padding: EdgeInsets.fromLTRB(20, 20, 20, 16),
                              child: Text(
                                'notes_title'.tr(),
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.black87,
                                ),
                              ),
                            ),
                            Padding(
                              padding: EdgeInsets.fromLTRB(20, 0, 20, 20),
                              child: TextField(
                                controller: _notesController,
                                maxLines: 4,
                                maxLength: 500,
                                decoration: InputDecoration(
                                  hintText: 'notes_hint'.tr(),
                                  hintStyle: TextStyle(color: Colors.grey[400]),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    borderSide: BorderSide(color: Colors.grey[300]!),
                                  ),
                                  focusedBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    borderSide: BorderSide(color: Color(0xFF00D4AA)),
                                  ),
                                  contentPadding: EdgeInsets.all(16),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      SizedBox(height: 32),

                      // Submit button
                      Container(
                        width: double.infinity,
                        height: 56,
                        child: Consumer<AccountabilityProvider>(
                          builder: (context, provider, child) {
                            return ElevatedButton(
                              onPressed: _isSubmitting || provider.isLoading ? null : _submitCheckIn,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Color(0xFF00D4AA),
                                foregroundColor: Colors.white,
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16),
                                ),
                              ),
                              child: _isSubmitting || provider.isLoading
                                  ? Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        SizedBox(
                                          width: 20,
                                          height: 20,
                                          child: CircularProgressIndicator(
                                            color: Colors.white,
                                            strokeWidth: 2,
                                          ),
                                        ),
                                        SizedBox(width: 12),
                                        Text(
                                          'send_checkin'.tr(),
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    )
                                  : Text(
                                      'send_checkin'.tr(),
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                            );
                          },
                        ),
                      ),

                      SizedBox(height: 20),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submitCheckIn() async {
    setState(() => _isSubmitting = true);

    try {
      final provider = Provider.of<AccountabilityProvider>(context, listen: false);
      final authService = AuthService(); // AuthService példány létrehozása
      
      final userId = await authService.getUserId(); // getUserId() hívás
      
      if (userId == null) {
        throw Exception('no_logged_in_user'.tr());
      }

      final checkIn = CheckIn(
        id: '',
        partnershipId: widget.partnershipId,
        userId: userId, // AuthService-ből kapott userId
        date: DateTime.now().toIso8601String().split('T')[0],
        goalsMet: _goalsMet,
        progressRating: _progressRating,
        notes: _notesController.text.isNotEmpty ? _notesController.text : null,
        createdAt: DateTime.now(),
      );

      final success = await provider.createCheckIn(widget.partnershipId, checkIn);

      if (success) {
        Navigator.of(context).pop(true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('checkin_success'.tr()),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(provider.error ?? 'checkin_error'.tr()),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('error_occurred'.tr(namedArgs: {'error': e.toString()})),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() => _isSubmitting = false);
    }
  }

  String _formatDate(DateTime date) {
    const months = [
      'január', 'február', 'március', 'április', 'május', 'június',
      'július', 'augusztus', 'szeptember', 'október', 'november', 'december'
    ];
    
    return '${date.year}. ${months[date.month - 1]} ${date.day}.';
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }
}
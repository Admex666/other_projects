// lib/widgets/swipeable_card.dart

import 'package:flutter/material.dart';
import '../models/accountability_models.dart';

class SwipeableCard extends StatefulWidget {
  final PartnerSuggestion suggestion;
  final bool isTopCard;
  final VoidCallback? onSwipeLeft;
  final VoidCallback? onSwipeRight;

  const SwipeableCard({
    Key? key,
    required this.suggestion,
    this.isTopCard = false,
    this.onSwipeLeft,
    this.onSwipeRight,
  }) : super(key: key);

  @override
  _SwipeableCardState createState() => _SwipeableCardState();
}

class _SwipeableCardState extends State<SwipeableCard>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _rotationAnimation;
  late Animation<double> _scaleAnimation;

  Offset _dragStart = Offset.zero;
  Offset _dragUpdate = Offset.zero;
  bool _isDragging = false;

  static const double _swipeThreshold = 100.0;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    
    _slideAnimation = Tween<Offset>(
      begin: Offset.zero,
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _rotationAnimation = Tween<double>(
      begin: 0,
      end: 0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }

  void _handlePanStart(DragStartDetails details) {
    if (!widget.isTopCard) return;
    
    _dragStart = details.localPosition;
    _isDragging = true;
  }

  void _handlePanUpdate(DragUpdateDetails details) {
    if (!widget.isTopCard || !_isDragging) return;

    setState(() {
      _dragUpdate = details.localPosition - _dragStart;
    });
  }

  void _handlePanEnd(DragEndDetails details) {
    if (!widget.isTopCard || !_isDragging) return;

    _isDragging = false;
    
    final swipeDistance = _dragUpdate.dx.abs();
    final swipeDirection = _dragUpdate.dx > 0 ? 1 : -1;

    if (swipeDistance > _swipeThreshold) {
      // Animate card off screen
      _animateCardExit(swipeDirection > 0);
    } else {
      // Snap back to center
      _animateCardReturn();
    }
  }

  void _animateCardExit(bool swipeRight) {
    final endOffset = swipeRight ? Offset(2.0, 0) : Offset(-2.0, 0);
    final endRotation = swipeRight ? 0.3 : -0.3;

    _slideAnimation = Tween<Offset>(
      begin: _getCardOffset(),
      end: endOffset,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _rotationAnimation = Tween<double>(
      begin: _getCardRotation(),
      end: endRotation,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.8,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _animationController.forward().then((_) {
      if (swipeRight && widget.onSwipeRight != null) {
        widget.onSwipeRight!();
      } else if (!swipeRight && widget.onSwipeLeft != null) {
        widget.onSwipeLeft!();
      }
      _resetCard();
    });
  }

  void _animateCardReturn() {
    _slideAnimation = Tween<Offset>(
      begin: _getCardOffset(),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.elasticOut,
    ));

    _rotationAnimation = Tween<double>(
      begin: _getCardRotation(),
      end: 0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.elasticOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.elasticOut,
    ));

    _animationController.forward().then((_) {
      _resetCard();
    });
  }

  void _resetCard() {
    _animationController.reset();
    setState(() {
      _dragUpdate = Offset.zero;
    });
  }

  Offset _getCardOffset() {
    if (_isDragging) {
      return Offset(_dragUpdate.dx / 300, _dragUpdate.dy / 600);
    }
    return _slideAnimation.value;
  }

  double _getCardRotation() {
    if (_isDragging) {
      return _dragUpdate.dx / 1000;
    }
    return _rotationAnimation.value;
  }

  Color _getSwipeIndicatorColor() {
    if (_dragUpdate.dx.abs() < _swipeThreshold) return Colors.transparent;
    return _dragUpdate.dx > 0 ? Colors.green : Colors.red;
  }

  String _getSwipeIndicatorText() {
    if (_dragUpdate.dx.abs() < _swipeThreshold) return '';
    return _dragUpdate.dx > 0 ? 'LIKE' : 'PASS';
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onPanStart: _handlePanStart,
      onPanUpdate: _handlePanUpdate,
      onPanEnd: _handlePanEnd,
      child: AnimatedBuilder(
        animation: _animationController,
        builder: (context, child) {
          return Transform.translate(
            offset: Offset(
              _getCardOffset().dx * MediaQuery.of(context).size.width,
              _getCardOffset().dy * MediaQuery.of(context).size.height,
            ),
            child: Transform.rotate(
              angle: _getCardRotation(),
              child: Transform.scale(
                scale: widget.isTopCard ? (_scaleAnimation.value) : 0.95,
                child: Opacity(
                  opacity: widget.isTopCard ? 1.0 : 0.8,
                  child: _buildCard(),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildCard() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 8, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 20,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Stack(
        children: [
          // Main card content
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with avatar and compatibility
              Container(
                padding: EdgeInsets.all(24),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFF00D4AA),
                      Color(0xFF00D4AA).withOpacity(0.8),
                    ],
                  ),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                  ),
                ),
                child: Row(
                  children: [
                    // Avatar
                    Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          widget.suggestion.username.isNotEmpty 
                              ? widget.suggestion.username[0].toUpperCase()
                              : '?',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF00D4AA),
                          ),
                        ),
                      ),
                    ),
                    SizedBox(width: 16),
                    
                    // Name and compatibility
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.suggestion.username,
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          SizedBox(height: 4),
                          Row(
                            children: [
                              Icon(
                                Icons.favorite,
                                color: Colors.white,
                                size: 16,
                              ),
                              SizedBox(width: 4),
                              Text(
                                '${widget.suggestion.compatibilityPercentage}% egyezés',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    // Compatibility badge
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        widget.suggestion.compatibilityText,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Bio
              if (widget.suggestion.bio != null)
                Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    widget.suggestion.bio!,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[700],
                      height: 1.5,
                    ),
                  ),
                ),

              // Goals
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Célok',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: widget.suggestion.goalCategories.map((goal) {
                        return Container(
                          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: Color(0xFF00D4AA).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: Color(0xFF00D4AA).withOpacity(0.3),
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(goal.emoji, style: TextStyle(fontSize: 16)),
                              SizedBox(width: 6),
                              Text(
                                goal.displayName,
                                style: TextStyle(
                                  color: Color(0xFF00D4AA),
                                  fontWeight: FontWeight.w600,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ),
              ),

              // Common goals
              if (widget.suggestion.commonGoals.isNotEmpty)
                Padding(
                  padding: EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Közös célok',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                      SizedBox(height: 12),
                      ...widget.suggestion.commonGoals.map((goal) {
                        return Padding(
                          padding: EdgeInsets.only(bottom: 8),
                          child: Row(
                            children: [
                              Icon(
                                Icons.check_circle,
                                color: Colors.green,
                                size: 20,
                              ),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  goal,
                                  style: TextStyle(
                                    color: Colors.grey[700],
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ],
                  ),
                ),

              Spacer(),

              // Action hint
              Padding(
                padding: EdgeInsets.all(24),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.swipe, color: Colors.grey[400], size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Húzd jobbra a like-hoz, balra a pass-hoz',
                      style: TextStyle(
                        color: Colors.grey[500],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Swipe indicator overlay
          if (widget.isTopCard && _dragUpdate.dx.abs() > _swipeThreshold)
            Positioned.fill(
              child: Container(
                decoration: BoxDecoration(
                  color: _getSwipeIndicatorColor().withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Center(
                  child: Container(
                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    decoration: BoxDecoration(
                      color: _getSwipeIndicatorColor(),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      _getSwipeIndicatorText(),
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }
}
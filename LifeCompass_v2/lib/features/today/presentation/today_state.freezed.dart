// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'today_state.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;
/// @nodoc
mixin _$TodayState {

 bool get isLoading; DailyIntention? get intention; List<Task> get tasks; List<Habit> get habits; Set<int> get completedHabitIds; String? get errorMessage;
/// Create a copy of TodayState
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$TodayStateCopyWith<TodayState> get copyWith => _$TodayStateCopyWithImpl<TodayState>(this as TodayState, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is TodayState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&const DeepCollectionEquality().equals(other.intention, intention)&&const DeepCollectionEquality().equals(other.tasks, tasks)&&const DeepCollectionEquality().equals(other.habits, habits)&&const DeepCollectionEquality().equals(other.completedHabitIds, completedHabitIds)&&(identical(other.errorMessage, errorMessage) || other.errorMessage == errorMessage));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,const DeepCollectionEquality().hash(intention),const DeepCollectionEquality().hash(tasks),const DeepCollectionEquality().hash(habits),const DeepCollectionEquality().hash(completedHabitIds),errorMessage);

@override
String toString() {
  return 'TodayState(isLoading: $isLoading, intention: $intention, tasks: $tasks, habits: $habits, completedHabitIds: $completedHabitIds, errorMessage: $errorMessage)';
}


}

/// @nodoc
abstract mixin class $TodayStateCopyWith<$Res>  {
  factory $TodayStateCopyWith(TodayState value, $Res Function(TodayState) _then) = _$TodayStateCopyWithImpl;
@useResult
$Res call({
 bool isLoading, DailyIntention? intention, List<Task> tasks, List<Habit> habits, Set<int> completedHabitIds, String? errorMessage
});




}
/// @nodoc
class _$TodayStateCopyWithImpl<$Res>
    implements $TodayStateCopyWith<$Res> {
  _$TodayStateCopyWithImpl(this._self, this._then);

  final TodayState _self;
  final $Res Function(TodayState) _then;

/// Create a copy of TodayState
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? isLoading = null,Object? intention = freezed,Object? tasks = null,Object? habits = null,Object? completedHabitIds = null,Object? errorMessage = freezed,}) {
  return _then(_self.copyWith(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,intention: freezed == intention ? _self.intention : intention // ignore: cast_nullable_to_non_nullable
as DailyIntention?,tasks: null == tasks ? _self.tasks : tasks // ignore: cast_nullable_to_non_nullable
as List<Task>,habits: null == habits ? _self.habits : habits // ignore: cast_nullable_to_non_nullable
as List<Habit>,completedHabitIds: null == completedHabitIds ? _self.completedHabitIds : completedHabitIds // ignore: cast_nullable_to_non_nullable
as Set<int>,errorMessage: freezed == errorMessage ? _self.errorMessage : errorMessage // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [TodayState].
extension TodayStatePatterns on TodayState {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _TodayState value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _TodayState() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _TodayState value)  $default,){
final _that = this;
switch (_that) {
case _TodayState():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _TodayState value)?  $default,){
final _that = this;
switch (_that) {
case _TodayState() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( bool isLoading,  DailyIntention? intention,  List<Task> tasks,  List<Habit> habits,  Set<int> completedHabitIds,  String? errorMessage)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _TodayState() when $default != null:
return $default(_that.isLoading,_that.intention,_that.tasks,_that.habits,_that.completedHabitIds,_that.errorMessage);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( bool isLoading,  DailyIntention? intention,  List<Task> tasks,  List<Habit> habits,  Set<int> completedHabitIds,  String? errorMessage)  $default,) {final _that = this;
switch (_that) {
case _TodayState():
return $default(_that.isLoading,_that.intention,_that.tasks,_that.habits,_that.completedHabitIds,_that.errorMessage);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( bool isLoading,  DailyIntention? intention,  List<Task> tasks,  List<Habit> habits,  Set<int> completedHabitIds,  String? errorMessage)?  $default,) {final _that = this;
switch (_that) {
case _TodayState() when $default != null:
return $default(_that.isLoading,_that.intention,_that.tasks,_that.habits,_that.completedHabitIds,_that.errorMessage);case _:
  return null;

}
}

}

/// @nodoc


class _TodayState implements TodayState {
  const _TodayState({this.isLoading = false, this.intention, final  List<Task> tasks = const [], final  List<Habit> habits = const [], final  Set<int> completedHabitIds = const {}, this.errorMessage}): _tasks = tasks,_habits = habits,_completedHabitIds = completedHabitIds;
  

@override@JsonKey() final  bool isLoading;
@override final  DailyIntention? intention;
 final  List<Task> _tasks;
@override@JsonKey() List<Task> get tasks {
  if (_tasks is EqualUnmodifiableListView) return _tasks;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_tasks);
}

 final  List<Habit> _habits;
@override@JsonKey() List<Habit> get habits {
  if (_habits is EqualUnmodifiableListView) return _habits;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_habits);
}

 final  Set<int> _completedHabitIds;
@override@JsonKey() Set<int> get completedHabitIds {
  if (_completedHabitIds is EqualUnmodifiableSetView) return _completedHabitIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableSetView(_completedHabitIds);
}

@override final  String? errorMessage;

/// Create a copy of TodayState
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$TodayStateCopyWith<_TodayState> get copyWith => __$TodayStateCopyWithImpl<_TodayState>(this, _$identity);



@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _TodayState&&(identical(other.isLoading, isLoading) || other.isLoading == isLoading)&&const DeepCollectionEquality().equals(other.intention, intention)&&const DeepCollectionEquality().equals(other._tasks, _tasks)&&const DeepCollectionEquality().equals(other._habits, _habits)&&const DeepCollectionEquality().equals(other._completedHabitIds, _completedHabitIds)&&(identical(other.errorMessage, errorMessage) || other.errorMessage == errorMessage));
}


@override
int get hashCode => Object.hash(runtimeType,isLoading,const DeepCollectionEquality().hash(intention),const DeepCollectionEquality().hash(_tasks),const DeepCollectionEquality().hash(_habits),const DeepCollectionEquality().hash(_completedHabitIds),errorMessage);

@override
String toString() {
  return 'TodayState(isLoading: $isLoading, intention: $intention, tasks: $tasks, habits: $habits, completedHabitIds: $completedHabitIds, errorMessage: $errorMessage)';
}


}

/// @nodoc
abstract mixin class _$TodayStateCopyWith<$Res> implements $TodayStateCopyWith<$Res> {
  factory _$TodayStateCopyWith(_TodayState value, $Res Function(_TodayState) _then) = __$TodayStateCopyWithImpl;
@override @useResult
$Res call({
 bool isLoading, DailyIntention? intention, List<Task> tasks, List<Habit> habits, Set<int> completedHabitIds, String? errorMessage
});




}
/// @nodoc
class __$TodayStateCopyWithImpl<$Res>
    implements _$TodayStateCopyWith<$Res> {
  __$TodayStateCopyWithImpl(this._self, this._then);

  final _TodayState _self;
  final $Res Function(_TodayState) _then;

/// Create a copy of TodayState
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? isLoading = null,Object? intention = freezed,Object? tasks = null,Object? habits = null,Object? completedHabitIds = null,Object? errorMessage = freezed,}) {
  return _then(_TodayState(
isLoading: null == isLoading ? _self.isLoading : isLoading // ignore: cast_nullable_to_non_nullable
as bool,intention: freezed == intention ? _self.intention : intention // ignore: cast_nullable_to_non_nullable
as DailyIntention?,tasks: null == tasks ? _self._tasks : tasks // ignore: cast_nullable_to_non_nullable
as List<Task>,habits: null == habits ? _self._habits : habits // ignore: cast_nullable_to_non_nullable
as List<Habit>,completedHabitIds: null == completedHabitIds ? _self._completedHabitIds : completedHabitIds // ignore: cast_nullable_to_non_nullable
as Set<int>,errorMessage: freezed == errorMessage ? _self.errorMessage : errorMessage // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on

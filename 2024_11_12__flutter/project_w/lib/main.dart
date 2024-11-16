import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:csv/csv.dart';
import 'package:intl/intl.dart';
import 'package:flutter_native_timezone/flutter_native_timezone.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz;


void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: 'Team List',
      home: TeamListPage(),
    );
  }
}

class TeamListPage extends StatefulWidget {
  const TeamListPage({super.key});

  @override
  _TeamListPageState createState() => _TeamListPageState();
}

class _TeamListPageState extends State<TeamListPage> {
  List<String> userTeamNames = [];
  List<String> selectedTeams = [];
  List<String> filteredTeams = [];
  bool isLoading = true;
  TextEditingController searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    loadCSV();
    searchController.addListener(updateFilteredTeams);
  }

  // Load the CSV data from the assets
  Future<void> loadCSV() async {
    final data = await rootBundle.loadString('assets/project_w_data.csv');
    List<List<dynamic>> csvTable = CsvToListConverter(eol: '\n', fieldDelimiter: ',').convert(data);

    // Extract team names
    List<String> teams = [];
    var headerRow = csvTable[0];
    var userTeamIndex = headerRow.indexOf('user_team');

    // Loop through rows and collect team names
    for (var row in csvTable.skip(1)) {
      var teamName = row[userTeamIndex]?.toString()?.trim();
      if (teamName != null && teamName.isNotEmpty) {
        teams.add(teamName);
      }
    }

    // Remove duplicates and sort
    var uniqueTeams = teams.toSet().toList();
    uniqueTeams.sort();

    // Update state with the list of teams
    setState(() {
      userTeamNames = uniqueTeams;
      filteredTeams = uniqueTeams;
      isLoading = false;
    });
  }

  // Filter teams based on search input
  void updateFilteredTeams() {
    String query = searchController.text.toLowerCase();
    setState(() {
      filteredTeams = userTeamNames
          .where((team) => team.toLowerCase().contains(query))
          .toList();
    });
  }

  // Toggle team selection
  void toggleSelection(String team) {
    setState(() {
      if (selectedTeams.contains(team)) {
        selectedTeams.remove(team);
      } else {
        selectedTeams.add(team);
      }
    });
  }

  // Reset selected teams
  void resetSelectedTeams() {
    setState(() {
      selectedTeams.clear(); // Clear the selected teams
    });
  }

  // Navigate to the schedule page
  void navigateToSchedulePage(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SchedulePage(selectedTeams: selectedTeams),
      ),
    );
  }

  @override
  void dispose() {
    searchController.removeListener(updateFilteredTeams);
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Teams'),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: TextField(
                    controller: searchController,
                    decoration: const InputDecoration(
                      labelText: 'Search Teams',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: filteredTeams.length,
                    itemBuilder: (context, index) {
                      String team = filteredTeams[index];
                      return ListTile(
                        title: Text(team),
                        leading: Checkbox(
                          value: selectedTeams.contains(team),
                          onChanged: (_) {
                            toggleSelection(team);
                          },
                        ),
                      );
                    },
                  ),
                ),
                const Divider(),
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(
                    'Selected Teams: ${selectedTeams.join(', ')}',
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: ElevatedButton(
                    onPressed: selectedTeams.isEmpty
                        ? null // Disable button if no teams are selected
                        : () => navigateToSchedulePage(context),
                    child: const Text('Load Schedule'),
                  ),
                ),
                // Reset Selected Teams Button
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: ElevatedButton(
                    onPressed: resetSelectedTeams, // Reset teams when pressed
                    child: const Text('Reset Selected Teams'),
                  ),
                ),
              ],
            ),
    );
  }
}



class SchedulePage extends StatefulWidget {
  final List<String> selectedTeams;

  const SchedulePage({super.key, required this.selectedTeams});

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> {
  Map<String, List<String>> formattedDataByDate = {};
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadAndFilterData();
  }

  RichText formatRowWithBoldTeams(String row, List<String> selectedTeams) {
    List<TextSpan> spans = [];
    List<String> parts = row.split(' @ ');
    
    // Handle away team
    if (selectedTeams.contains(parts[0])) {
      spans.add(TextSpan(text: parts[0], style: const TextStyle(fontWeight: FontWeight.bold)));
    } else {
      spans.add(TextSpan(text: parts[0]));
    }
    
    spans.add(const TextSpan(text: ' @ '));
    
    // Handle home team and the rest
    List<String> homeParts = parts[1].split(' (');
    if (selectedTeams.contains(homeParts[0])) {
      spans.add(TextSpan(text: homeParts[0], style: const TextStyle(fontWeight: FontWeight.bold)));
    } else {
      spans.add(TextSpan(text: homeParts[0]));
    }
    
    spans.add(TextSpan(text: ' (${homeParts[1]}'));

    return RichText(
      text: TextSpan(
        style: const TextStyle(fontSize: 14, color: Colors.black),
        children: spans,
      ),
    );
  }

  Future<String> convertToUserTimezone(String timeString, String dateString) async {
    tz.initializeTimeZones();

    DateTime mountainTime = DateFormat('HH:mm:ss yyyy-MM-dd').parse('$timeString $dateString');
    
    final mountainTimeZone = tz.getLocation('America/Denver');
    final mountainDateTime = tz.TZDateTime.from(mountainTime, mountainTimeZone);

    String localTimeZoneName = await FlutterNativeTimezone.getLocalTimezone();
    final localTimeZone = tz.getLocation(localTimeZoneName);

    final localDateTime = tz.TZDateTime.from(mountainDateTime, localTimeZone);

    return DateFormat('h:mm a').format(localDateTime);
  }

  Future<void> loadAndFilterData() async {
    final data = await rootBundle.loadString('assets/project_w_data.csv');

    List<List<dynamic>> csvTable =
        CsvToListConverter(eol: '\n', fieldDelimiter: ',').convert(data);

    final headerRow = csvTable[0];
    final userTeamIndex = headerRow.indexOf('user_team');
    final dateIndex = headerRow.indexOf('Date');
    final awayTeamIndex = headerRow.indexOf('Away Team');
    final homeTeamIndex = headerRow.indexOf('Home Team');
    final sportIndex = headerRow.indexOf('Sport');
    final timeIndex = headerRow.indexOf('Time');
    final gameTypeIndex = headerRow.indexOf('game_type');

    final today = DateTime.now();
    final endDate = today.add(const Duration(days: 5));
    final filteredRows = csvTable.skip(1).where((row) {
      final teamName = row[userTeamIndex]?.toString()?.trim();
      final rowDate = DateTime.tryParse(row[dateIndex]?.toString() ?? '');
      return widget.selectedTeams.contains(teamName) &&
          rowDate != null &&
          rowDate.isAfter(today.subtract(const Duration(days: 1))) &&
          rowDate.isBefore(endDate.add(const Duration(days: 1)));
    }).toList();

    final groupedData = <String, List<String>>{};
    for (var row in filteredRows) {
      final rowDate = DateTime.tryParse(row[dateIndex]?.toString() ?? '');
      if (rowDate != null) {
        final formattedDate = DateFormat("EEEE, MMM d'th'").format(rowDate);

        final awayTeam = row[awayTeamIndex]?.toString();
        final homeTeam = row[homeTeamIndex]?.toString();
        final sport = row[sportIndex]?.toString();
        final time = row[timeIndex]?.toString();
        final gameType = row[gameTypeIndex]?.toString();
        
        // Convert time to user's timezone
        final convertedTime = await convertToUserTimezone(time!, row[dateIndex].toString());
        
        final formattedRow = "$awayTeam @ $homeTeam ($sport - $gameType) - $convertedTime";

        groupedData.putIfAbsent(formattedDate, () => []).add(formattedRow);
      }
    }


    setState(() {
      formattedDataByDate = groupedData;
      isLoading = false;
    });
  }




  @override
  Widget build(BuildContext context) {
    final String today = DateFormat("EEEE, MMMM d'th', yyyy").format(DateTime.now());
    final String selectedTeamsText = widget.selectedTeams.isNotEmpty
        ? "Selected Teams: ${widget.selectedTeams.join(', ')}"
        : "Selected Teams: None";

    return Scaffold(
      appBar: AppBar(
        title: const Text('Schedule Page'),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Text(
                      "Today is $today\n$selectedTeamsText",
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Divider(),
                  Expanded(
                    child: ListView(
                      children: formattedDataByDate.entries.map((entry) {
                        final date = entry.key;
                        final rows = entry.value;

                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                date,
                                style: const TextStyle(
                                    fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 8),
                              ...rows.map((row) => Padding(
                                padding: const EdgeInsets.only(bottom: 4.0),
                                child: formatRowWithBoldTeams(row, widget.selectedTeams),
                              )),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

}
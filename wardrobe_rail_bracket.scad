/*
 * Ceiling-mounted clamp for a 30 x 15 mm wardrobe rail.
 *
 * Coordinate system in assembly mode:
 *   X: across the rail, Y: along the rail, Z: upward toward the ceiling.
 *   The ceiling-contact face is Z = 0 and the bracket hangs below it.
 *
 * Set `part` to "main" or "cap" before exporting an individual STL.
 * The default "print" layout places both parts on the build plate.
 */

part = "print";                 // print/assembly/main/cap/main_print/cap_print

rail_width = 15;                // horizontal cross-section dimension
rail_height = 30;               // vertical cross-section dimension
rail_radius = 7;                // rounded-rectangle corner radius
rail_clearance = 0.3;           // clearance on each side
ceiling_gap = 10;               // ceiling to top of rail

plate_width = 50;
plate_length = 75;
plate_thickness = 8;
plate_corner_radius = 4;
ceiling_screw_diameter = 4.5;   // clearance for nominal 4 mm screws
ceiling_screw_spacing = 40;
ceiling_screw_head_diameter = 8.5;
ceiling_screw_access_clearance = 1;
ceiling_screw_angle = 90;

wall_thickness = 6;
clamp_depth = 24;               // length of clamp along the rail
clamp_gap = 0.6;                // closing gap between main body and cap
cap_capture_height = 10.3;      // rail height captured below the split
gusset_thickness = 6;
gusset_rail_clearance = 0.4;

clamp_bolt_diameter = 4;
clamp_bolt_clearance = 0.5;
clamp_bolt_head_diameter = 8;
clamp_bolt_head_height = 4.2;
bolt_lug_radius = 10.5;
m4_nut_across_flats = 7.2;
m4_nut_thickness = 3.4;
nut_clearance = 0.2;
print_support_angle = 30;       // maximum boss overhang from vertical

$fn = 64;

// Derived dimensions. Changing the public rail parameters updates the clamp.
socket_width = rail_width + 2 * rail_clearance;
socket_height = rail_height + 2 * rail_clearance;
socket_radius = rail_radius + rail_clearance;
outer_width = socket_width + 2 * wall_thickness;
outer_height = socket_height + 2 * wall_thickness + 2;
outer_radius = socket_radius + wall_thickness;
rail_center_z = -(ceiling_gap + rail_height / 2);
split_relative_z = -socket_height / 2 + cap_capture_height;
split_z = rail_center_z + split_relative_z;
outer_profile_bottom_z = rail_center_z - outer_height / 2;
cap_floor_z = outer_profile_bottom_z + 1;
nut_corner_radius = (m4_nut_across_flats + nut_clearance) / sqrt(3);
bolt_x = socket_width / 2 + wall_thickness
    + max(clamp_bolt_head_diameter / 2, nut_corner_radius);
nut_pocket_height = m4_nut_thickness + nut_clearance;
nut_center_z = split_z + wall_thickness + nut_pocket_height / 2;
main_lug_top_z = nut_center_z + nut_pocket_height / 2 + wall_thickness;
boss_support_height = -plate_thickness - main_lug_top_z;
boss_support_top_radius =
    bolt_lug_radius - boss_support_height * tan(print_support_angle);
ceiling_countersink_depth =
    (ceiling_screw_head_diameter - ceiling_screw_diameter)
    / (2 * tan(ceiling_screw_angle / 2));

assert(
    part == "print" || part == "assembly" || part == "main" || part == "cap"
    || part == "main_print" || part == "cap_print",
    "part must be print, assembly, main, cap, main_print, or cap_print"
);
assert(rail_width > 0 && rail_height > 0, "rail dimensions must be positive");
assert(rail_radius > 0, "rail_radius must be positive");
assert(
    rail_radius <= min(rail_width, rail_height) / 2,
    "rail_radius must be at most half the smaller rail dimension"
);
assert(rail_clearance >= 0, "rail_clearance cannot be negative");
assert(wall_thickness >= 6, "wall_thickness must be at least 6 mm");
assert(ceiling_gap >= 0, "ceiling_gap cannot be negative");
assert(
    plate_width > 0 && plate_length > 0 && plate_thickness > 0,
    "plate dimensions must be positive"
);
assert(plate_thickness >= wall_thickness, "plate is thinner than wall_thickness");
assert(
    plate_corner_radius >= 0
    && plate_corner_radius <= min(plate_width, plate_length) / 2,
    "plate_corner_radius does not fit the plate"
);
assert(clamp_depth > 0, "clamp_depth must be positive");
assert(
    clamp_depth >= 2 * bolt_lug_radius,
    "clamp_depth must be at least the bolt lug diameter"
);
assert(
    gusset_thickness >= wall_thickness,
    "gusset_thickness must be at least wall_thickness"
);
assert(gusset_rail_clearance >= 0, "gusset_rail_clearance cannot be negative");
assert(
    ceiling_screw_diameter > 0
    && ceiling_screw_head_diameter > ceiling_screw_diameter,
    "ceiling screw dimensions are invalid"
);
assert(
    ceiling_screw_angle > 0 && ceiling_screw_angle < 180,
    "ceiling_screw_angle must be between 0 and 180 degrees"
);
assert(
    ceiling_countersink_depth > 0 && ceiling_countersink_depth < plate_thickness,
    "ceiling countersink does not fit the plate"
);
assert(ceiling_screw_access_clearance >= 0, "ceiling screw access clearance is negative");
assert(
    ceiling_screw_spacing + ceiling_screw_head_diameter <= plate_length - 4,
    "ceiling screw spacing does not fit the plate"
);
assert(
    clamp_bolt_diameter > 0
    && clamp_bolt_clearance >= 0
    && clamp_bolt_head_diameter > clamp_bolt_diameter
    && clamp_bolt_head_height > 0,
    "clamp bolt dimensions are invalid"
);
assert(
    m4_nut_across_flats > 0 && m4_nut_thickness > 0 && nut_clearance >= 0,
    "nut dimensions are invalid"
);
assert(
    bolt_lug_radius >= clamp_bolt_head_diameter / 2 + wall_thickness,
    "bolt lug is too small around the bolt head"
);
assert(
    bolt_lug_radius >= nut_corner_radius + wall_thickness,
    "bolt lug is too small around the captive nut"
);
assert(
    nut_center_z - nut_pocket_height / 2 - split_z >= wall_thickness,
    "not enough material below the captive nut"
);
assert(
    main_lug_top_z - nut_center_z - nut_pocket_height / 2 >= wall_thickness,
    "not enough material above the captive nut"
);
assert(
    print_support_angle > 0 && print_support_angle <= 30,
    "print_support_angle must be between 0 and 30 degrees"
);
assert(boss_support_height > 0, "bolt boss support height must be positive");
assert(
    boss_support_top_radius > clamp_bolt_diameter / 2 + wall_thickness / 2,
    "bolt boss support is too narrow at the plate"
);
assert(
    bolt_x + boss_support_top_radius <= plate_width / 2,
    "bolt boss support must begin within the ceiling plate"
);
assert(
    plate_width >= outer_width,
    "plate_width must cover the upper saddle"
);
assert(
    bolt_x - nut_corner_radius - socket_width / 2 >= wall_thickness,
    "not enough material between socket and captive nut"
);
assert(
    bolt_x - clamp_bolt_head_diameter / 2 - socket_width / 2 >= wall_thickness,
    "not enough material between socket and bolt head"
);
assert(
    cap_capture_height > rail_radius && cap_capture_height < socket_height / 2,
    "cap_capture_height must place the split on a straight side of the socket"
);
assert(clamp_gap >= 0 && clamp_gap < 2, "clamp_gap must be between 0 and 2 mm");


module rounded_rectangle_2d(size, radius) {
    assert(radius <= min(size) / 2, "rounded rectangle radius is too large");
    hull() {
        for (x = [-size[0] / 2 + radius, size[0] / 2 - radius])
            for (y = [-size[1] / 2 + radius, size[1] / 2 - radius])
                translate([x, y]) circle(r = radius);
    }
}


module extrude_along_y(length) {
    rotate([90, 0, 0])
        linear_extrude(height = length, center = true, convexity = 10)
            children();
}


module centered_cube(size) {
    translate([-size[0] / 2, -size[1] / 2, -size[2] / 2]) cube(size);
}


module plate_positive() {
    translate([0, 0, -plate_thickness])
        linear_extrude(height = plate_thickness)
            rounded_rectangle_2d([plate_width, plate_length], plate_corner_radius);
}


module socket_void(length = clamp_depth + 2) {
    translate([0, 0, rail_center_z])
        extrude_along_y(length)
            rounded_rectangle_2d([socket_width, socket_height], socket_radius);
}


module rail_reference(length = plate_length + 20) {
    translate([0, 0, rail_center_z])
        extrude_along_y(length)
            rounded_rectangle_2d([rail_width, rail_height], rail_radius);
}


module clamp_outer() {
    translate([0, 0, rail_center_z])
        extrude_along_y(clamp_depth)
            rounded_rectangle_2d([outer_width, outer_height], outer_radius);
}


module main_clamp_segment() {
    intersection() {
        clamp_outer();
        translate([-50, -plate_length, split_z])
            cube([100, 2 * plate_length, 100]);
    }
}


module cap_clamp_segment() {
    intersection() {
        clamp_outer();
        translate([-50, -plate_length, cap_floor_z])
            cube([100, 2 * plate_length, split_z - clamp_gap - cap_floor_z]);
    }
}


module vertical_lug_bridge(x_inner, x_outer, bottom_z, top_z) {
    hull() {
        for (x = [x_inner, x_outer])
            translate([x, 0, bottom_z])
                cylinder(h = top_z - bottom_z, r = bolt_lug_radius);
    }
}


module main_bolt_lugs() {
    for (side = [-1, 1]) {
        vertical_lug_bridge(
            side * (outer_width / 2 - 3.5),
            side * bolt_x,
            split_z,
            main_lug_top_z
        );

        // In print orientation this frustum grows outward at 45 degrees from
        // the plate, supporting the otherwise floating outer bolt boss.
        translate([side * bolt_x, 0, main_lug_top_z])
            cylinder(
                h = boss_support_height,
                r1 = bolt_lug_radius,
                r2 = boss_support_top_radius
            );
    }
}


module cap_bolt_lugs() {
    for (side = [-1, 1])
        vertical_lug_bridge(
            side * (outer_width / 2 - 3.5),
            side * bolt_x,
            cap_floor_z,
            split_z - clamp_gap
        );
}


module longitudinal_gussets() {
    gusset_x = socket_width / 2 + gusset_rail_clearance + gusset_thickness / 2;
    inner_height = -plate_thickness - split_z;
    for (y_side = [-1, 1]) {
        for (x_side = [-1, 1]) {
            hull() {
                translate([
                    x_side * gusset_x,
                    y_side * (clamp_depth / 2 - gusset_thickness / 2),
                    (split_z - plate_thickness) / 2
                ])
                    centered_cube([gusset_thickness, gusset_thickness, inner_height]);
                translate([
                    x_side * gusset_x,
                    y_side * (plate_length / 2 - 6),
                    -plate_thickness
                ])
                    centered_cube([gusset_thickness, gusset_thickness, gusset_thickness]);
            }
        }
    }
}


module ceiling_screw_voids() {
    for (y = [-ceiling_screw_spacing / 2, ceiling_screw_spacing / 2]) {
        // Carry both the screw shank and its head through any gusset below the
        // plate. The wider access chimney meets the countersink at Z=-8.
        translate([0, y, -100])
            cylinder(h = 101, d = ceiling_screw_diameter);
        translate([0, y, -100])
            cylinder(
                h = 100 - plate_thickness + 0.02,
                d = ceiling_screw_head_diameter + ceiling_screw_access_clearance
            );
        translate([0, y, -plate_thickness - 0.01])
            cylinder(
                h = ceiling_countersink_depth + 0.02,
                d1 = ceiling_screw_head_diameter,
                d2 = ceiling_screw_diameter
            );
    }
}


module clamp_bolt_voids() {
    for (side = [-1, 1])
        translate([side * bolt_x, 0, cap_floor_z - 1])
            cylinder(
                h = main_lug_top_z - cap_floor_z + 2,
                d = clamp_bolt_diameter + clamp_bolt_clearance
            );
}


module clamp_bolt_head_recesses() {
    for (side = [-1, 1])
        translate([side * bolt_x, 0, cap_floor_z - 0.01])
            cylinder(h = clamp_bolt_head_height + 0.02, d = clamp_bolt_head_diameter);
}


module captive_nut_pockets() {
    for (side = [-1, 1]) {
        translate([
            side * bolt_x,
            0,
            nut_center_z - nut_pocket_height / 2
        ])
            cylinder(h = nut_pocket_height, r = nut_corner_radius, $fn = 6);

        // A front-loading channel lets the nut slide into the hexagonal trap.
        translate([
            side * bolt_x - nut_corner_radius,
            -clamp_depth / 2 - 1,
            nut_center_z - nut_pocket_height / 2
        ])
            cube([
                2 * nut_corner_radius,
                clamp_depth / 2 + 1,
                nut_pocket_height
            ]);
    }
}


module main_bracket() {
    difference() {
        union() {
            plate_positive();
            main_clamp_segment();
            main_bolt_lugs();
            longitudinal_gussets();
        }
        socket_void();
        ceiling_screw_voids();
        clamp_bolt_voids();
        captive_nut_pockets();
    }
}


module clamp_cap() {
    difference() {
        union() {
            cap_clamp_segment();
            cap_bolt_lugs();
        }
        socket_void();
        clamp_bolt_voids();
        clamp_bolt_head_recesses();
    }
}


module assembled_bracket(show_rail = true) {
    color([0.92, 0.62, 0.12]) main_bracket();
    color([0.95, 0.72, 0.22]) clamp_cap();
    if ($preview && show_rail)
        color([0.70, 0.72, 0.75, 0.45]) rail_reference();
}


module print_layout() {
    // Main body is inverted so the ceiling face and countersinks print cleanly.
    translate([-plate_width / 2 - 7, 0, 0])
        main_print();

    // The cap has a deliberately flattened exterior face for bed adhesion.
    translate([plate_width / 2 + 7, 0, 0]) cap_print();
}


module main_print() {
    rotate([180, 0, 0]) main_bracket();
}


module cap_print() {
    translate([0, 0, -cap_floor_z]) clamp_cap();
}


if (part == "main")
    main_bracket();
else if (part == "cap")
    clamp_cap();
else if (part == "assembly")
    assembled_bracket();
else if (part == "main_print")
    main_print();
else if (part == "cap_print")
    cap_print();
else
    print_layout();
